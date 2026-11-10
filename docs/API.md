# API AgendaSH

Base local: `http://localhost:8000` · Documentação interativa (testar no navegador): `http://localhost:8000/docs`

> **Estado atual (MVP):** todas as rotas estão **abertas**, sem token. Isso muda nas tarefas T3/T7 (ver `TASKS.md`). Cada rota abaixo indica o que vai mudar. Até lá, **não coloque dados reais de produção**.

## Convenções

- Corpo e resposta em JSON. Datas em ISO 8601 **sem fuso**: `2026-11-12T14:30:00`.
- Campos de data/hora recebidos de `reuniao` e `convite` vêm como `datetime`.
- `PUT` substitui o recurso (exceto `/usuarios`, que só altera o que for enviado).
- `DELETE` bem-sucedido devolve `204` sem corpo.

### Formato de erro (sempre o mesmo)
```json
{ "detail": "A sala já está reservada nesse horário", "codigo": "CONFLITO", "request_id": "a1b2c3d4e5f6" }
```
`detail` é a mensagem para mostrar ao usuário. `codigo` é estável (use no código, não no texto). `request_id` também vem no cabeçalho `X-Request-ID` e aparece nos logs do servidor: **ao reportar um bug, informe esse id**.

| Status | Quando | `codigo` |
|---|---|---|
| 400 | Dado inválido ou referência inexistente (ex.: sala que não existe) | `REQUISICAO_INVALIDA` / `DADOS_INVALIDOS` |
| 401 | E-mail ou senha inválidos (e, futuramente, token ausente/expirado) | `NAO_AUTENTICADO` |
| 403 | Sem permissão (futuro, T12) | `SEM_PERMISSAO` |
| 404 | Recurso ou rota não existe | `NAO_ENCONTRADO` |
| 405 | Método HTTP errado para a rota | `METODO_NAO_PERMITIDO` |
| 409 | Conflito: duplicado, horário ocupado, registro em uso | `CONFLITO`, `REGISTRO_DUPLICADO`, `REFERENCIA_INVALIDA` |
| 422 | Corpo/parâmetro com formato errado. `detail` lista os campos; `erros` é a lista | `DADOS_INVALIDOS` |
| 429 | Muitas tentativas (futuro, T20) | `MUITAS_TENTATIVAS` |
| 503 | Banco fora do ar | `BANCO_INDISPONIVEL` |
| 500 | Erro interno (mensagem genérica; detalhes só no log do servidor) | `ERRO_INTERNO` |

### Middlewares (já ativos, em `backend/app/core/`)
Ordem de fora para dentro: **CORS → RequestContext → CatchAll → rotas**.
- **CORS** (`main.py`): só aceita as origens da variável `CORS_ORIGINS` (padrão `http://localhost:5500,http://127.0.0.1:5500`). Fica por fora para que *até as respostas de erro* tenham CORS; sem isso o navegador mostra "NetworkError" em vez do erro real.
- **RequestContext** (`middleware.py`): cria o `X-Request-ID`, mede o tempo, grava uma linha de log por requisição (método, caminho, status, ms; **nunca corpo nem query string**) e adiciona cabeçalhos de segurança: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control: no-store`, `Content-Security-Policy` (`default-src 'none'`), `Permissions-Policy`, `Cross-Origin-Resource-Policy`, `Cross-Origin-Opener-Policy` e, em HTTPS, `Strict-Transport-Security`. Eles protegem o **navegador** (clickjacking, sniffing, vazamento de referrer); **não** validam e-mail. Quem barra e-mail falso é a regra de e-mail acima.
- **CatchAll** (`middleware.py`): qualquer exceção não tratada vira JSON padronizado. Erros do Postgres são convertidos (duplicado → 409, FK → 409, dado inválido → 400, banco fora → 503). Nunca devolve traceback, SQL ou texto do banco.
- **Handlers** (`errors.py`): 422 em português e 404/405 no mesmo formato.

---

## Infra

### `GET /health`
Verifica se a API está no ar. `200 {"status":"ok"}`. Não toca no banco.

---

## Auth

### `POST /auth/login`
```json
{ "email": "ana@escola.edu.br", "senha": "segredo123" }
```
`200` → dados do usuário (sem senha):
```json
{ "id_usuario": 1, "nome": "Ana", "email": "ana@escola.edu.br", "criado_em": "2026-11-05T10:00:00" }
```
Erros: `401` e-mail ou senha inválidos (mesma mensagem nos dois casos, de propósito).
> **Vai mudar (T3/T13):** devolve `{ "access_token": "...", "token_type": "bearer" }`; só entra com e-mail verificado. Nova rota `GET /auth/me`.

---

### `POST /auth/esqueci-senha`
Pede o link para redefinir a senha. Corpo: `{ "email": "ana@undb.edu.br" }`.
Resposta **sempre** `200 {"detail": "Se o e-mail estiver cadastrado, enviamos um link..."}`, exista a conta ou não (não revela quem tem cadastro). O link é `FRONT_URL/esqueciSenha.html?token=...`, vale 30 min (`RESET_TTL_MINUTOS`) e só pode ser usado uma vez.
Sem `SMTP_HOST` no `.env` (desenvolvimento) o e-mail **não é enviado**: o link aparece no log do uvicorn (linha `WARNING ... Link de recuperação`).

### `POST /auth/redefinir-senha`
Troca a senha com o token do link. Corpo: `{ "token": "...", "nova_senha": "mínimo 6 caracteres" }`.
`200` se deu certo. `400` (`REQUISICAO_INVALIDA`) se o link for inválido, expirado ou já usado. `422` se a senha for curta.
Contas antigas com hash em outro formato (ex.: bcrypt) não conseguem logar (`401`); use esta recuperação para gravar uma senha válida.

## Usuários — `/usuarios`

Modelo de resposta `UsuarioOut`: `id_usuario`, `nome`, `email`, `criado_em`. **O hash da senha nunca sai** (teste automático em T26).

| Método e rota | Corpo | Resposta | Erros |
|---|---|---|---|
| `GET /usuarios` | – | `200` lista de `UsuarioOut` ordenada por nome | – |
| `GET /usuarios/{id}` | – | `200` `UsuarioOut` | `404` |
| `POST /usuarios` | `{nome (1-100), email (≤100), senha (≥6)}` | `201` `UsuarioOut` | `409` e-mail já cadastrado, `422` |
| `PUT /usuarios/{id}` | `{nome?, email?}` (só o que enviar muda) | `200` `UsuarioOut` | `404`, `409`, `422` |
| `DELETE /usuarios/{id}` | – | `204` | `404`, `409` se tem reuniões/convites |

**Regra de e-mail (T6, `backend/app/core/email_policy.py`):** `POST /usuarios` e `PUT /usuarios/{id}` só aceitam e-mail da UNDB, sempre salvo em minúsculas:

| Tipo | Formato aceito | Exemplo |
|---|---|---|
| Aluno | `002-02` + dígitos, domínio exato `aluno.undb.edu.br` | `002-021234@aluno.undb.edu.br` |
| Professor/colaborador | nome começando com letra (letras, números, `.` `_` `-`), domínio exato `undb.edu.br` | `maria.silva@undb.edu.br` |

Recusado com `422` (`DADOS_INVALIDOS`): Gmail, Outlook, Yahoo e qualquer outro provedor; domínios de golpe (`undb.edu.br.golpe.net`, `xundb.edu.br`, `evil.undb.edu.br`); letras de outro alfabeto e `xn--`; mais de um `@`, espaço, vírgula, `<>`, aspas, quebra de linha; `+tag`; matrícula fora do padrão. Configurável por `EMAIL_DOMINIO_ALUNO`, `EMAIL_PREFIXO_ALUNO` e `EMAIL_DOMINIOS_PROFESSOR` (ver `.env.example`). Esta regra prova o **formato**; que a pessoa **recebe** na caixa será provado pelo código de confirmação (T9/T13).

> **Vai mudar:** `GET /usuarios` devolve só `id` e `nome` (T10/T14); `PUT`/`DELETE` só na própria conta (T12); cadastro com código por e-mail, domínios permitidos e senha mínima 8 (T6/T9); resposta de cadastro idêntica exista a conta ou não (T9).

---

## Salas — `/salas`

`SalaOut`: `id_sala`, `nome`, `capacidade`, `tipo`, `localizacao_link`.

| Método e rota | Corpo | Resposta | Erros |
|---|---|---|---|
| `GET /salas` | – | `200` lista | – |
| `GET /salas/{id}` | – | `200` | `404` |
| `POST /salas` | `{nome (1-100), capacidade (>0), tipo (≤250), localizacao_link?}` | `201` | `422` |
| `PUT /salas/{id}` | mesmo corpo do POST | `200` | `404`, `422` |
| `DELETE /salas/{id}` | – | `204` | `404`, `409` se tem reuniões |

> **Vai mudar (T11):** modo e local/link passam a ficar na própria reunião; salas só para espaços reais. Hoje o front cria uma sala por local digitado (gambiarra do MVP).

---

## Reuniões — `/reunioes`

`ReuniaoOut`: `id_reuniao`, `id_usuario` (organizador), `id_sala`, `titulo`, `descricao`, `data_inicio`, `data_fim`.

| Método e rota | Corpo | Resposta | Erros |
|---|---|---|---|
| `GET /reunioes?id_sala=` | – | `200` lista por `data_inicio` (filtro opcional por sala) | `422` |
| `GET /reunioes/{id}` | – | `200` | `404` |
| `POST /reunioes` | veja abaixo | `201` | `409` sala ocupada, `400` usuário/sala inexistente, `422` |
| `PUT /reunioes/{id}` | mesmo corpo do POST | `200` | `404`, `409`, `400`, `422` |
| `DELETE /reunioes/{id}` | – | `204` (apaga também os convites) | `404` |

Corpo de `POST`/`PUT`:
```json
{ "id_usuario": 1, "id_sala": 2, "titulo": "Daily", "descricao": null,
  "data_inicio": "2026-11-12T14:30:00", "data_fim": "2026-11-12T15:30:00" }
```
Regras: `titulo` 1-200 caracteres; `data_fim` precisa ser **depois** de `data_inicio` (`422`); a sala não pode ter outra reunião sobrepondo o intervalo (`409`; fim exatamente igual ao início seguinte **não** conflita).

> **Vai mudar:** `id_usuario` sai do corpo (vem do token, T7); lista filtrada por participante (T14); só o organizador altera/cancela (T12); convidados na mesma chamada e conflito também por pessoa (T19).

---

## Convites — `/convites`

`ConviteOut`: `id_reuniao`, `id_usuario`, `status_resposta` (`pendente` | `aceito` | `recusado`), `data_hora` (quando respondeu).

| Método e rota | Corpo | Resposta | Erros |
|---|---|---|---|
| `GET /convites?id_reuniao=&id_usuario=` | – | `200` lista (filtros opcionais) | `422` |
| `POST /convites` | `{id_reuniao, id_usuario}` (nasce `pendente`) | `201` | `409` já convidado, `400` reunião/usuário inexistente |
| `PUT /convites/{id_reuniao}/{id_usuario}` | `{status_resposta}` | `200` | `404`, `422` status inválido |
| `DELETE /convites/{id_reuniao}/{id_usuario}` | – | `204` | `404` |

> **Vai mudar:** só organizador e convidados veem (T14); só o convidado responde o próprio convite (T12).

---

## Como usar

### Pelo navegador (mais fácil para testar)
Abra `http://localhost:8000/docs`, escolha a rota, clique em **Try it out**, edite o corpo e **Execute**.

### Pelo front (JavaScript) — `frontend/src/core/api.js`
```js
// GET
const salas = await api("/salas");
// POST com corpo (o corpo é convertido para JSON sozinho)
const r = await api("/reunioes", { method: "POST", body: { id_usuario: 1, id_sala: 2, titulo: "Daily",
    data_inicio: "2026-11-12T14:30:00", data_fim: "2026-11-12T15:30:00" } });
// Tratar erro: a função lança Error com a mensagem pronta para mostrar; erro.status e erro.codigo também existem
try { await api("/reunioes", { method: "POST", body }); }
catch (e) { if (e.status === 409) avisarConflito(e.message); else mostrarErro(e.message); }
```

### Pelo terminal (PowerShell: use `curl.exe`)
```powershell
curl.exe http://localhost:8000/health
curl.exe -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d "{\"email\":\"ana@escola.edu.br\",\"senha\":\"segredo123\"}"
```

### Fluxo típico de agendamento
1. `POST /usuarios` (criar conta) → `POST /auth/login`
2. `GET /salas` (ou `POST /salas` para criar uma)
3. `POST /reunioes` → se `409`, mostrar "sala ocupada" e pedir outro horário
4. `POST /convites` para cada participante
5. Convidado: `GET /convites?id_usuario=<meu id>` → `PUT /convites/{reuniao}/{eu}` com `aceito` ou `recusado`

## Testes e logs
- `cd backend && python -m pytest -q`: testes dos middlewares e do tratamento de erros (não usam o banco).
- Cada requisição gera uma linha no terminal do uvicorn: `GET /salas -> 200 (12 ms) [a1b2c3d4e5f6]`. Erros 5xx incluem o traceback **só no log**, nunca na resposta.
