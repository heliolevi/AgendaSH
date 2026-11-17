# Segurança — AgendaSH

Relatório do pentest/revisão de segurança e o que foi corrigido.
Data da revisão: 2026-11-16.

---

## 1. O que JÁ estava correto (mantido)

- **SQL 100% parametrizado** — nenhuma query concatena entrada do usuário; as f-strings
  só interpolam a constante `COLS` (lista fixa de colunas). Sem SQL injection.
- **Senhas** com `pbkdf2_sha256` (passlib) e verificação em tempo constante.
- **Login/token** via OAuth2 *password flow* + JWT HS256 assinado com `hmac` e conferido
  com `compare_digest`; `exp` obrigatório. (É o "auth2" que você pediu — já existe.)
- **Anti força-bruta** no login (`throttle.py`): 5 falhas / 15 min bloqueiam a chave ip|email.
- **Códigos de e-mail** guardados só como HMAC-SHA256, uso único, 5 tentativas, rate-limit.
- **Política de e-mail UNDB** com defesas contra spoofing (igualdade de domínio, só ASCII,
  bloqueio de punycode e injeção de cabeçalho).
- **Headers de segurança + CSP** em toda resposta; erros padronizados sem vazar traceback/SQL.

---

## 2. Corrigido nesta branch (`melhorias-seguranca-ui`)

### 2.1 IDOR / autorização por objeto — **ALTO** ✅
Antes, qualquer usuário logado podia editar/apagar reunião, evento ou reunião fixa de
**outra pessoa**, e ler/enumerar convites de qualquer um (`GET /convites?id_usuario=X`).

Agora:
- `PUT`/`DELETE` de `/reunioes`, `/eventos` e `/reunioes-fixas` exigem ser **dono ou admin**.
- `/convites`: só o **organizador** convida; só o **próprio convidado** responde; listar
  mostra apenas os próprios convites (admin vê tudo).
- Regressão coberta em `backend/tests/test_autorizacao.py`.

### 2.2 Mass assignment / organizador falsificado — **MÉDIO** ✅
O `id_usuario` do organizador vinha do **corpo** da requisição (dava para criar reunião em
nome de outro). Agora o organizador é sempre o **usuário do token**; o campo foi removido dos
schemas `*Create` e das chamadas do frontend.

---

## 3. AÇÃO MANUAL OBRIGATÓRIA — segredos no histórico do git — **CRÍTICO** ⚠️

O arquivo `.env` foi versionado nos commits `f974950` e `c3bf291` e o repositório tem remote
em `github.com/heliolevi/AgendaSH`. Mesmo com o `.gitignore` atual, **os segredos continuam
recuperáveis** por `git log -p` e, se o push foi feito, estão no GitHub.

Segredos expostos: `DATABASE_URL` (senha do Postgres) e `SMTP_PASSWORD`.

### Passo 1 — ROTACIONE as credenciais (prioridade máxima)
Trocar o histórico **não basta**: quem já clonou/viu tem os segredos. Então:
- [ ] Trocar a senha do usuário do Postgres e atualizar `DATABASE_URL` no `.env`.
- [ ] Gerar nova senha de app do SMTP (ex.: "senha de app" do Gmail) e atualizar `SMTP_PASSWORD`.
- [ ] Definir `JWT_SECRET` e `CODIGO_SECRET` longos e aleatórios no `.env` de produção
      (hoje caem para um valor aleatório por processo — some ao reiniciar).

Gerar segredos fortes:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Passo 2 — Apagar o `.env` do histórico
Com git-filter-repo (recomendado):
```bash
pip install git-filter-repo
cd AgendaSH
git filter-repo --path .env --invert-paths --force
git remote add origin https://github.com/heliolevi/AgendaSH.git   # filter-repo remove o remote
git push origin --force --all
git push origin --force --tags
```
> Alternativa: BFG Repo-Cleaner — `bfg --delete-files .env` e depois
> `git reflog expire --expire=now --all && git gc --prune=now --aggressive`.
> Avise o time: todo mundo precisa reclonar depois do force-push.

### Passo 3 — Confirmar
```bash
git log --all --oneline -- .env      # não deve retornar nada
```

---

## 4. Recomendações (não bloqueiam a entrega)

- **Token no `localStorage`**: se houver qualquer XSS, o JWT é roubável. O código escapa HTML
  (`esc()`), então o risco hoje é baixo. Em produção, considerar cookie `HttpOnly`+`SameSite`.
- **/docs e /openapi.json** ficam abertos. Para um sistema interno tudo bem; se publicar,
  proteja com login ou desative em produção.
- **Produção atrás de HTTPS** (o HSTS já é enviado quando o proxy marca `x-forwarded-proto: https`).
- **CORS**: em produção, definir `CORS_ORIGINS` com o domínio real do front (hoje aponta p/ dev local).
