# AgendaSH

Sistema de agendamento de reuniões da software house (UNDB). Entrega: **qui 19/11/2026**.

- **Backend:** FastAPI + PostgreSQL (Neon), SQL puro com `psycopg`.
- **Frontend:** HTML, CSS e JavaScript puro, feito para celular (mobile first).
- **Acesso:** só e-mail institucional da UNDB (ver [Regra de e-mail](#regra-de-e-mail)).

## Onde achar cada coisa

| Quero... | Leia |
|---|---|
| Saber **o que fazer** e quem faz | [`docs/TASKS.md`](docs/TASKS.md) (tarefas T1 a T34, prazos, dependências) |
| Ver **todas as rotas**, erros e exemplos | [`docs/API.md`](docs/API.md) |
| Detalhes do backend | [`backend/README.md`](backend/README.md) |
| Detalhes do frontend | [`frontend/README.md`](frontend/README.md) |

## Estrutura

```
AgendaSH/
├── backend/
│   ├── app/
│   │   ├── main.py            # cria o app, registra middlewares e rotas
│   │   ├── core/              # database.py, security.py, errors.py, middleware.py, email_policy.py
│   │   └── modules/           # 1 módulo = 1 tabela: auth, usuarios, salas, reunioes, convites
│   │       └── <modulo>/      # schemas.py (entrada/saída) · repository.py (SQL) · router.py (rotas)
│   ├── tests/                 # pytest (não usa o banco)
│   └── .env.example           # modelo das variáveis de ambiente
├── frontend/
│   ├── *.html                 # welcome, login, cadastro, esqueciSenha, index (início), calendario, reunioes, perfil
│   ├── style.css
│   └── src/
│       ├── core/api.js        # cliente HTTP (api(), usuarioLogado())
│       ├── shared/app.js      # guarda de login, barra inferior, leitura de reuniões
│       └── modules/           # um módulo por área (auth, reunioes...)
├── docs/                      # API.md e TASKS.md
├── requirements.txt           # dependências do backend
├── requirements-dev.txt       # + pytest, httpx (testes)
├── create_table.py            # cria as tabelas no Neon (uso único)
└── test_db.py                 # lista as tabelas do banco (teste de conexão)
```

## Rodando na sua máquina (Windows / PowerShell)

Pré-requisitos: **Python 3.11+** e **Git**. Node **não** é necessário.

> No PowerShell 5.1 **não existe `&&`**. Rode um comando por linha, e use um terminal para o backend e outro para o frontend.

### 1. Clonar
```powershell
git clone https://github.com/heliolevi/AgendaSH.git
cd AgendaSH
```

### 2. Backend (terminal 1)
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
O prompt deve começar com `(.venv)`. A API fica em `http://localhost:8000` e a documentação interativa em `http://localhost:8000/docs`.

### 3. Frontend (terminal 2)
```powershell
cd frontend
python -m http.server 5500
```
Abra `http://localhost:5500/welcome.html`.

> Use **sempre** a porta **5500** para o front: o backend só aceita essa origem (CORS).

### 4. Testes do backend
```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m pytest -q
```
Devem passar todos (75 hoje). Rode antes de abrir um PR.

## Variáveis de ambiente (`backend/.env`)

O `.env` **nunca vai para o git** (já está no `.gitignore`). Peça a `DATABASE_URL` ao Hélio.

```
DATABASE_URL=postgresql://usuario:senha@host.neon.tech/neondb?sslmode=require
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
EMAIL_DOMINIO_ALUNO=aluno.undb.edu.br
EMAIL_PREFIXO_ALUNO=002-02
EMAIL_DOMINIOS_PROFESSOR=undb.edu.br
```
Cuidados: use **`=`** (não `:`), **sem espaços**, **sem aspas**, uma variável por linha. Depois de editar o `.env`, **reinicie o uvicorn** (o `--reload` não observa esse arquivo).

## Regra de e-mail

O cadastro e a troca de e-mail só aceitam:

| Tipo | Formato | Exemplo |
|---|---|---|
| Aluno | `002-02` + números @ `aluno.undb.edu.br` | `002-021234@aluno.undb.edu.br` |
| Professor/colaborador | `nome@undb.edu.br` | `maria.silva@undb.edu.br` |

Gmail, Outlook, Yahoo e domínios de golpe (`undb.edu.br.golpe.net`, `xundb.edu.br`...) são recusados com erro 422. A regra está em `backend/app/core/email_policy.py`. Detalhes em `docs/API.md`.

## Como trabalhamos

1. Pegue sua tarefa em [`docs/TASKS.md`](docs/TASKS.md) (cada uma tem número `T..`, responsável e prazo).
2. Atualize a `main` e crie uma branch **a partir dela**:
   ```powershell
   git checkout main
   git pull origin main
   git checkout -b feat/t07-rotas-protegidas
   ```
   Nome da branch: `feat/tNN-assunto` (nova funcionalidade) ou `fix/assunto` (correção).
3. Faça commits pequenos, em português, no formato `tipo: o que mudou` (`feat`, `fix`, `docs`, `test`). Exemplo: `feat(auth): login devolve token JWT`.
4. Rode os testes (`python -m pytest -q`).
5. Envie a branch e abra um **Pull Request** para a `main`:
   ```powershell
   git push origin feat/t07-rotas-protegidas
   ```
6. **O Hélio revisa** os PRs de backend antes do merge. Não faça push direto na `main`.
7. Marque a tarefa como feita em `docs/TASKS.md` no mesmo PR.

## Regras do código (leia antes de escrever)

**Backend**
- Um módulo = uma tabela. Rota em `router.py`, SQL em `repository.py`, formato dos dados em `schemas.py`. Regra de negócio mais complexa vai num `service.py`.
- **Nunca** `SELECT *` em código novo: liste as colunas. **Nunca** devolva `senha_hash`, códigos de verificação ou dados de outras pessoas.
- **Erros:** levante `HTTPException(status, "mensagem em português")`. Erros de banco, 404, 405, 422 e falhas inesperadas já são tratados pelos middlewares e viram `{detail, codigo, request_id}` (sem traceback). Não imprima senhas nem corpo de requisição em log.
- Rota nova = **teste novo** em `backend/tests/`.
- Perguntou "por que deu 500?" Veja o terminal do uvicorn: cada requisição tem uma linha com o `request_id`, e o erro completo aparece no log (nunca na resposta).

**Frontend**
- Sempre chame a API pela função `api()` de `src/core/api.js`. Ela já mostra mensagem amigável se o servidor cair e expõe `erro.status` e `erro.codigo`.
- Não guarde dados sensíveis no navegador (a T8 troca o `localStorage` do cadastro completo por um token).
- Não escreva HTML com texto vindo da API sem escapar: use `esc()` de `src/shared/app.js`.
- Mantenha o visual do protótipo (cores e fontes em `style.css`, variáveis em `:root`).

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `NetworkError when attempting to fetch resource` | Backend desligado, front em outra porta (não 5500) ou erro no servidor. Veja o terminal do uvicorn |
| `500` e `'NoneType' object has no attribute 'encode'` | `DATABASE_URL` não foi lida. Confira o `.env` (`=`, sem espaço, sem aspas, nome do arquivo `.env` e não `.env.txt`) e reinicie o uvicorn |
| `uvicorn` não é reconhecido | Venv desativado. Rode `.venv\Scripts\Activate.ps1` ou use `python -m uvicorn ...` |
| `&&` não é um separador válido | Você está no PowerShell 5.1: rode um comando por linha |
| Script de ativação bloqueado | `Set-ExecutionPolicy -Scope Process Bypass` (vale só para aquele terminal) |
| `422` ao cadastrar | E-mail fora do padrão UNDB ou senha curta. A mensagem diz o campo |
| `503` / "Serviço temporariamente indisponível" | Neon fora do ar ou sem internet |
| `409` ao agendar | Sala já reservada nesse horário (esperado: mostre o aviso) |
| Mudei o `.env` e nada mudou | Reinicie o uvicorn |

## Estado atual (MVP)

Já funciona: cadastro e login (e-mail UNDB), telas mobile, agendar e cancelar reunião com checagem de conflito, perfil, middlewares de erro, testes.
**Ainda falta** (ver `docs/TASKS.md`): token JWT e rotas protegidas (hoje **todas as rotas estão abertas**, não use dados reais), verificação de e-mail por código, convites nas telas, permissões, deploy.
