# Como rodar o AgendaSH

Guia passo a passo para subir o backend (FastAPI) e o frontend (HTML/JS puro) na sua máquina, no Windows com PowerShell.

## Pré-requisitos

- **Python 3.11+** (testado com 3.13)
- **Git**
- A `DATABASE_URL` do banco Neon (peça ao Hélio). Sem ela a API sobe, mas qualquer rota que use o banco falha.
- Node **não** é necessário.

> No PowerShell 5.1 **não existe `&&`**. Rode um comando por linha. Use **dois terminais**: um para o backend e outro para o frontend.

## 1. Clonar o projeto

```powershell
git clone https://github.com/heliolevi/AgendaSH.git
cd AgendaSH
```

## 2. Backend (terminal 1)

```powershell
cd backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r ..\requirements-dev.txt
copy .env.example .env
notepad .env
python -m uvicorn app.main:app --reload
```

O prompt deve começar com `(.venv)`. Quando subir, você verá `Application startup complete`.

- API: http://localhost:8000
- Documentação interativa (testar rotas no navegador): http://localhost:8000/docs
- Verificação rápida: http://localhost:8000/health deve responder `{"status":"ok"}`

Nas próximas vezes, basta ativar o venv e subir o servidor (dentro de `backend`):

```powershell
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

## 3. Configurar o `.env`

O arquivo é `backend/.env` e **nunca vai para o git**. Conteúdo:

```
DATABASE_URL=postgresql://usuario:senha@host.neon.tech/neondb?sslmode=require
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
EMAIL_DOMINIO_ALUNO=aluno.undb.edu.br
EMAIL_PREFIXO_ALUNO=002-02
EMAIL_DOMINIOS_PROFESSOR=undb.edu.br
```

| Variável | Para que serve | Obrigatória |
|---|---|---|
| `DATABASE_URL` | Conexão com o PostgreSQL (Neon) | Sim |
| `CORS_ORIGINS` | Origens do front aceitas, separadas por vírgula. Padrão: `localhost:5500` e `127.0.0.1:5500` | Não |
| `EMAIL_DOMINIO_ALUNO` | Domínio dos e-mails de aluno | Não |
| `EMAIL_PREFIXO_ALUNO` | Prefixo da matrícula no e-mail de aluno | Não |
| `EMAIL_DOMINIOS_PROFESSOR` | Domínios aceitos para professor/colaborador | Não |

Cuidados:
- Use `=` (não `:`), **sem espaços**, **sem aspas**, uma variável por linha.
- O arquivo precisa se chamar `.env`, e não `.env.txt`.
- Depois de editar o `.env`, **reinicie o uvicorn**. O `--reload` não observa esse arquivo.
- O `.env` é lido a partir da pasta `backend`. Rode o uvicorn de dentro dela.

### Código por e-mail (cadastro e esqueci a senha)

Criar conta e redefinir senha exigem um **código de 6 dígitos enviado por e-mail (SMTP)**. Sem SMTP configurado, as duas coisas falham com erro 503. Configure no `backend/.env`:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seuemail@gmail.com
SMTP_PASSWORD=<senha de app do Gmail>
SMTP_FROM=seuemail@gmail.com
SMTP_TLS=1
CODIGO_SECRET=<valor longo e aleatório>
```

No Gmail é preciso ativar a verificação em 2 etapas e criar uma **senha de app** (https://myaccount.google.com/apppasswords). Não use a senha normal da conta e nunca coloque essas credenciais no git.

**Tabela nova (uma vez por banco):** os códigos ficam em `verificacao_email`. Crie com:

```powershell
cd backend
python -m app.modules.verificacao.criar_tabela
```

**Reuniões fixas (uma vez por banco):** cria a tabela `reuniao_fixa` e a coluna `reuniao.id_fixa` (só adiciona):

```powershell
cd backend
python -m app.modules.reunioes_fixas.criar_tabela
```

**Sem SMTP, só para testar na sua máquina:** `CODIGO_NO_LOG=1` no `.env` escreve o código no terminal do uvicorn em vez de enviar o e-mail. Nunca use isso em produção.

## 4. Frontend (terminal 2)

```powershell
cd frontend
python -m http.server 5500
```

Abra http://localhost:5500/welcome.html (ou `login.html`).

> Use **sempre a porta 5500**. O backend só aceita essa origem por causa do CORS. A URL da API usada pelo front (`http://localhost:8000`) fica em `frontend/src/core/api.js`.

## 5. Rodar os testes do backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m pytest -q
```

Os testes não usam o banco. Rode antes de abrir um PR.

## 6. Testar o cadastro

O cadastro só aceita e-mail institucional da UNDB:

| Tipo | Exemplo |
|---|---|
| Aluno | `002-021234@aluno.undb.edu.br` |
| Professor/colaborador | `maria.silva@undb.edu.br` |

Gmail, Outlook e domínios parecidos são recusados com erro 422. A regra está em `backend/app/core/email_policy.py`.

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `SyntaxError` ao subir, com `<<<<<<<` ou `>>>>>>>` no código | Merge com conflito não resolvido. Procure os marcadores, escolha o lado correto, salve e faça `git add` |
| `500` e `'NoneType' object has no attribute 'encode'` | `DATABASE_URL` não foi lida. Confira o `.env` (nome, `=`, sem espaço, sem aspas), rode o uvicorn dentro de `backend` e reinicie |
| `NetworkError when attempting to fetch resource` | Backend desligado, front fora da porta 5500, ou erro no servidor. Veja o terminal do uvicorn |
| `uvicorn` não é reconhecido | Venv desativado. Rode `.venv\Scripts\Activate.ps1` ou use `python -m uvicorn ...` |
| `&&` não é um separador válido | PowerShell 5.1: rode um comando por linha |
| Script de ativação bloqueado | `Set-ExecutionPolicy -Scope Process Bypass` (vale só para aquele terminal) |
| `503` / "Serviço temporariamente indisponível" | Neon fora do ar ou sem internet |
| `422` ao cadastrar | E-mail fora do padrão UNDB, senha com menos de 6 caracteres ou código sem 6 dígitos |
| Mudei o `.env` ou o código e nada mudou | Reinicie o uvicorn. O `--reload` demora ou não percebe mudanças dentro do OneDrive; se precisar, suba sem ele |
| `503` "O envio de e-mail não está configurado" | Faltam as variáveis `SMTP_*` no `.env` (ou o SMTP recusou o login). Veja o log do uvicorn |
| `429` ao pedir código | Espere 1 minuto entre pedidos (máximo 5 por hora por e-mail) |
| `401` no login de conta antiga | A conta tem hash de senha em formato antigo (bcrypt). Use "Recuperar senha" |
| Porta 8000 ou 5500 já em uso | Feche o processo anterior ou use outra porta (e ajuste `CORS_ORIGINS` e `api.js`) |

Ao investigar um erro 500, veja o terminal do uvicorn: cada requisição tem uma linha com o `request_id`, e o erro completo aparece no log.

## Veja também

- [`API.md`](API.md): todas as rotas, formato de erro e exemplos
- [`TASKS.md`](TASKS.md): tarefas, responsáveis e prazos
- [`../backend/README.md`](../backend/README.md) e [`../frontend/README.md`](../frontend/README.md)
