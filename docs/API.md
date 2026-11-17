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

### `POST /auth/cadastro/enviar-codigo`
Passo 1 do cadastro. Corpo: `{ "email": "joao@undb.edu.br" }`. Só aceita e-mail da UNDB (`422` se não for) e recusa e-mail já cadastrado (`409`). Manda um **código de 6 dígitos por SMTP** para esse e-mail e responde `200 {"detail", "expira_em_minutos"}`.

### `POST /auth/esqueci-senha`
Corpo: `{ "email": "..." }`. Manda o código de 6 dígitos para o e-mail da conta. A resposta é **sempre a mesma**, exista a conta ou não (não revela quem tem cadastro).

### `POST /auth/redefinir-senha`
Corpo: `{ "email": "...", "codigo": "123456", "nova_senha": "mínimo 6 caracteres" }`. `200` se o código estiver certo. `400` (`Código inválido ou expirado.`) se estiver errado, expirado ou já usado. `422` se o código não tiver 6 dígitos ou a senha for curta.

### Regras dos códigos (cadastro e senha)
- Vale 10 minutos (`CODIGO_TTL_MINUTOS`) e **só uma vez**. Pedir outro invalida o anterior.
- Um código de cadastro não serve para trocar senha, e o código de um e-mail não vale para outro.
- **5 tentativas erradas** invalidam o código.
- No máximo **1 envio por minuto** e **5 por hora** por e-mail (`429` além disso).
- No banco fica só o hash (tabela `verificacao_email`), nunca o código.
- **Sem `SMTP_HOST` o envio falha com `503`**: não existe criação de conta nem troca de senha sem receber o e-mail. Só para desenvolvimento, `CODIGO_NO_LOG=1` escreve o código no log do uvicorn.
- Contas antigas com hash em outro formato (ex.: bcrypt) dão `401` no login; use "Recuperar senha" para gravar uma senha válida.

## Eventos — `/eventos`

Tabela `eventos` (já existia no banco). Funciona como uma reunião sem convites: o evento é da equipe e aparece para todos na aba **Eventos**.

| Método e rota | Corpo | Resposta | Erros |
|---|---|---|---|
| `GET /eventos` | `?id_sala=` opcional | `200` lista ordenada por início | – |
| `GET /eventos/{id}` | – | `200` | `404` |
| `POST /eventos` | `{id_usuario, id_sala, titulo, descricao?, data_inicio, data_fim}` | `201` | `400` usuário/sala inexistente, `409` sala ocupada, `422` dia passado ou `data_fim <= data_inicio` |
| `PUT /eventos/{id}` | mesmo corpo do POST | `200` | `404`, `409`, `422` |
| `DELETE /eventos/{id}` | – | `204` | `404` |

## Reuniões fixas — `/reunioes-fixas`

Reunião que se repete **toda semana** no mesmo dia e horário. Ao criar, o servidor gera as reuniões reais (linhas normais de `reuniao`, com `id_fixa`) das próximas 8 semanas (`FIXAS_SEMANAS`) e as renova automaticamente a cada hora. Elas aparecem no calendário, aceitam convites e entram na checagem de conflito.

| Método e rota | Corpo | Resposta | Erros |
|---|---|---|---|
| `GET /reunioes-fixas` | `?id_usuario=` opcional | `200` séries vigentes | – |
| `POST /reunioes-fixas` | `{id_usuario, id_sala, titulo, descricao?, dia_semana (0=segunda…6=domingo), hora_inicio, hora_fim, data_inicio, data_fim?}` | `201` + `reunioes_criadas` e `datas_ignoradas` (datas em que a sala já estava ocupada) | `409` se **nenhuma** data coube, `422` início no passado, hora/data inválida |
| `DELETE /reunioes-fixas/{id}` | – | `204`. Apaga a série e as reuniões dela de hoje em diante | `404` |

Banco: rode uma vez `cd backend && python -m app.modules.reunioes_fixas.criar_tabela` (cria `reuniao_fixa` e a coluna `reuniao.id_fixa`; só adiciona).

## Regras de data (reuniões, eventos e fixas)

- **Não se agenda em dia que já passou.** `POST`/`PUT` de reunião, evento e fixa com início anterior a hoje às 00:00 (fuso `APP_TIMEZONE`, padrão `America/Fortaleza`) recebem `422` ("Não é possível agendar em um dia que já passou."). Hoje, em qualquer horário, é aceito.
- **Uma sala não tem duas coisas ao mesmo tempo**: o conflito (`409`) vale entre reuniões **e** eventos.
- **Limpeza automática:** ao iniciar e de hora em hora, o servidor apaga **definitivamente** reuniões (com convites) e eventos que terminaram antes de hoje às 00:00. Desligar: `LIMPEZA_REUNIOES=0`.

---

## Usuários — `/usuarios`

Modelo de resposta `UsuarioOut`: `id_usuario`, `nome`, `email`, `criado_em`. **O hash da senha nunca sai** (teste automático em T26).

| Método e rota | Corpo | Resposta | Erros |
|---|---|---|---|
| `GET /usuarios` | – | `200` lista de `UsuarioOut` ordenada por nome | – |
| `GET /usuarios/{id}` | – | `200` `UsuarioOut` | `404` |
| `POST /usuarios` | `{nome (1-100), email (≤100), senha (≥6), codigo (6 dígitos)}`. O `codigo` vem do e-mail enviado por `POST /auth/cadastro/enviar-codigo` | `201` `UsuarioOut` | `400` código inválido/expirado, `409` e-mail já cadastrado, `422` |
| `PUT /usuarios/{id}` | `{nome?, email?}` (só o que enviar muda) | `200` `UsuarioOut` | `404`, `409`, `422` |
| `DELETE /usuarios/{id}` | – | `204` | `404`, `409` se tem reuniões/convites |

**Regra de e-mail (T6, `backend/app/core/email_policy.py`):** `POST /usuarios` e `PUT /usuarios/{id}` só aceitam e-mail da UNDB, sempre salvo em minúsculas:

| Tipo | Formato aceito | Exemplo |
|---|---|---|
| Aluno | `002-02` + dígitos, domínio exato `aluno.undb.edu.br` | `002-021234@aluno.undb.edu.br` |
| Professor/colaborador | nome começando com letra (letras, números, `.` `_` `-`), domínio exato `undb.edu.br` | `maria.silva@undb.edu.br` |

Recusado com `422` (`DADOS_INVALIDOS`): Gmail, Outlook, Yahoo e qualquer outro provedor; domínios de golpe (`undb.edu.br.golpe.net`, `xundb.edu.br`, `evil.undb.edu.br`); letras de outro alfabeto e `xn--`; mais de um `@`, espaço, vírgula, `<>`, aspas, quebra de linha; `+tag`; matrícula fora do padrão. Configurável por `EMAIL_DOMINIO_ALUNO`, `EMAIL_PREFIXO_ALUNO` e `EMAIL_DOMINIOS_PROFESSOR` (ver `.env.example`). Esta regra prova o **formato**; que a pessoa **recebe** na caixa será provado pelo código de confirmação (T9/T13).

> **Vai mudar:** `GET /usuarios` devolve só `id` e `nome` (T10/T14); `PUT`/`DELETE` só na própria conta (T12); senha mínima 8 (T6/T9); resposta de cadastro idêntica exista a conta ou não (T9). O código por e-mail no cadastro já está implementado.

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
1. `POST /auth/cadastro/enviar-codigo` → código no e-mail → `POST /usuarios` (criar conta, com o código) → `POST /auth/login`
2. `GET /salas` (ou `POST /salas` para criar uma)
3. `POST /reunioes` → se `409`, mostrar "sala ocupada" e pedir outro horário
4. `POST /convites` para cada participante
5. Convidado: `GET /convites?id_usuario=<meu id>` → `PUT /convites/{reuniao}/{eu}` com `aceito` ou `recusado`

## Testes e logs
- `cd backend && python -m pytest -q`: testes dos middlewares e do tratamento de erros (não usam o banco).
- Cada requisição gera uma linha no terminal do uvicorn: `GET /salas -> 200 (12 ms) [a1b2c3d4e5f6]`. Erros 5xx incluem o traceback **só no log**, nunca na resposta.

## Autenticação (token JWT) — adicionado na blindagem de segurança

Todas as rotas de negócio agora exigem login por token. Público apenas:
`POST /auth/login`, `POST /auth/token`, `POST /auth/cadastro/enviar-codigo`,
`POST /auth/esqueci-senha`, `POST /auth/redefinir-senha`, `POST /usuarios` (cadastro) e `GET /health`.

### Como funciona
1. `POST /auth/login` com `{ "email": "...", "senha": "..." }` devolve:
   `{ "access_token": "<jwt>", "token_type": "bearer", "usuario": { ... } }`.
2. O front guarda o token e envia em toda chamada: `Authorization: Bearer <jwt>`.
3. `Depends(usuario_atual)` libera rotas para qualquer logado; `Depends(somente_admin)` só para papel `admin`.
4. Token expira em `JWT_EXPIRA_MIN` minutos (padrão 720 = 12h). Assinatura HS256 com `JWT_SECRET`.

Proteção anti força-bruta: 5 tentativas erradas de login por IP+e-mail em 15 min → bloqueio de 15 min (429).

### Papéis e /admin
- Coluna `usuario.papel` (`membro` | `admin`). Rode a migração: `python migrar.py`.
- Promova o primeiro admin: `python migrar.py seu-email@undb.edu.br`.
- Rotas admin (exigem papel `admin`):
  | Rota | Função |
  |---|---|
  | `GET /admin/resumo` | contadores (usuários, reuniões, salas, convites) |
  | `GET /admin/usuarios` | lista usuários com papel |
  | `PATCH /admin/usuarios/{id}` | define papel `{ "papel": "admin"\|"membro" }` |
  | `DELETE /admin/usuarios/{id}` | remove usuário |

### Testar no /docs
Use o botão **Authorize** (fluxo OAuth2 password): `username` = e-mail, `password` = senha.

### Variáveis novas no .env
```
JWT_SECRET=<valor longo e aleatório — nunca comitar>
JWT_EXPIRA_MIN=720
```
