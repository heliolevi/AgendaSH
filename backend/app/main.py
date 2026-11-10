import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.errors import registrar_handlers
from app.core.middleware import CatchAllMiddleware, RequestContextMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.convites.router import router as convites_router
from app.modules.reunioes.router import router as reunioes_router
from app.modules.salas.router import router as salas_router
from app.modules.usuarios.router import router as usuarios_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="AgendaSH", description="Agendamento interno de reuniões da software house")

registrar_handlers(app)

# add_middleware empilha: o último adicionado é o mais externo. CORS precisa ficar por fora.
app.add_middleware(CatchAllMiddleware)
app.add_middleware(RequestContextMiddleware)
# Origens do front separadas por vírgula (ex.: CORS_ORIGINS=https://agenda.exemplo.com). Padrão: dev local.
_origens = os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origens if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

for r in (auth_router, usuarios_router, salas_router, reunioes_router, convites_router):
    app.include_router(r)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}
