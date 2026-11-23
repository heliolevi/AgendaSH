import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # antes dos imports abaixo: auth/verificação leem JWT_SECRET e CODIGO_SECRET ao importar

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.core.auth import usuario_atual
from app.core.errors import registrar_handlers
from app.core.middleware import CatchAllMiddleware, RequestContextMiddleware
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.convites.router import router as convites_router
from app.modules.eventos.router import router as eventos_router
from app.modules.reunioes import limpeza
from app.modules.reunioes.router import router as reunioes_router
from app.modules.reunioes_fixas.router import router as reunioes_fixas_router
from app.modules.salas.router import router as salas_router
from app.modules.usuarios.router import router as usuarios_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Reunioes de dias que ja passaram sao apagadas ao iniciar e depois de tempos em tempos.
    tarefa = asyncio.create_task(limpeza.ciclo_de_limpeza()) if limpeza.ATIVA else None
    yield
    if tarefa:
        tarefa.cancel()


app = FastAPI(
    title="AgendaSH", description="Agendamento interno de reunioes da software house", lifespan=lifespan
)

registrar_handlers(app)

# add_middleware empilha: o ultimo adicionado e o mais externo. CORS precisa ficar por fora.
app.add_middleware(CatchAllMiddleware)
app.add_middleware(RequestContextMiddleware)
# Origens do front separadas por virgula (ex.: CORS_ORIGINS=https://agenda.exemplo.com). Padrao: dev local.
_origens = os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origens if o.strip()],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
)

# Rotas publicas: login/cadastro/recuperacao de senha.
app.include_router(auth_router)
# usuarios: o cadastro (POST) e publico; ver/editar/excluir se protegem dentro do proprio router.
app.include_router(usuarios_router)
# Area administrativa: cada rota exige papel 'admin'.
app.include_router(admin_router)
# Demais rotas de negocio: exigem apenas estar logado (token valido).
for r in (salas_router, reunioes_router, reunioes_fixas_router, eventos_router, convites_router):
    app.include_router(r, dependencies=[Depends(usuario_atual)])


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}
