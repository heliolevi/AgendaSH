# Backend AgendaSH (FastAPI + PostgreSQL/Neon)

## Rodar (PowerShell, dentro de `backend`; um comando por linha)
```
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r ..\requirements-dev.txt
copy .env.example .env      # preencher DATABASE_URL (nunca commitar o .env)
python -m uvicorn app.main:app --reload
```
Passo a passo completo, variáveis do `.env` e problemas comuns: README da raiz.
Docs interativas: http://localhost:8000/docs

Rotas, formato de erro e middlewares: `docs/API.md`. Testes: `python -m pytest -q` (dentro de `backend`, com o venv ativo; `pip install -r ../requirements-dev.txt`).

## Estrutura (1 módulo = 1 tabela)
```
app/
├── main.py              # registra os routers
├── core/                # database.py (conexão), security.py (hash de senha)
└── modules/
    ├── auth/            # login
    ├── usuarios/        # tabela usuario
    ├── salas/           # tabela sala
    ├── reunioes/        # tabela reuniao (+ regra de conflito de horário)
    └── convites/        # tabela convite (PK composta reuniao+usuario)
        ├── schemas.py     # entrada/saída da API (Pydantic)
        ├── repository.py  # SQL puro, só acesso ao banco
        └── router.py      # endpoints HTTP
```
Quando um módulo ganhar regra de negócio mais complexa, criar `service.py` entre router e repository.

## Endpoints
| Módulo | Rotas |
|---|---|
| auth | `POST /auth/login` |
| usuarios | `GET/POST /usuarios`, `GET/PUT/DELETE /usuarios/{id}` |
| salas | `GET/POST /salas`, `GET/PUT/DELETE /salas/{id}` |
| reunioes | `GET/POST /reunioes` (`?id_sala=`), `GET/PUT/DELETE /reunioes/{id}` |
| convites | `GET/POST /convites` (`?id_reuniao=&id_usuario=`), `PUT/DELETE /convites/{id_reuniao}/{id_usuario}` |
