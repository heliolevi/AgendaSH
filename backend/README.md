# Backend AgendaSH (FastAPI + PostgreSQL/Neon)

## Rodar
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # preencher DATABASE_URL (nunca commitar o .env)
uvicorn app.main:app --reload
```
Docs interativas: http://localhost:8000/docs

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
