from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.database import get_conn
from app.core.security import verificar_senha
from app.modules.usuarios import repository as usuarios_repo
from app.modules.usuarios.schemas import UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    senha: str


@router.post("/login", response_model=UsuarioOut)
def login(dados: LoginIn, conn=Depends(get_conn)):
    # TODO(back): emitir JWT e proteger as demais rotas com Depends(usuario_atual)
    usuario = usuarios_repo.buscar_por_email(conn, dados.email)
    if not usuario or not verificar_senha(dados.senha, usuario["senha_hash"]):
        raise HTTPException(401, "E-mail ou senha inválidos")
    return usuario
