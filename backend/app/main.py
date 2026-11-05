from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.router import router as auth_router
from app.modules.convites.router import router as convites_router
from app.modules.reunioes.router import router as reunioes_router
from app.modules.salas.router import router as salas_router
from app.modules.usuarios.router import router as usuarios_router

app = FastAPI(title="AgendaSH", description="Agendamento interno de reuniões da software house")

# TODO(front/back): restringir às origens reais do front quando houver ambiente definido
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

for r in (auth_router, usuarios_router, salas_router, reunioes_router, convites_router):
    app.include_router(r)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok"}
