import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core import reset_token
from app.core.database import get_conn
from app.core.email_sender import enviar_link_recuperacao
from app.core.security import hash_senha, verificar_senha
from app.modules.usuarios import repository as usuarios_repo
from app.modules.usuarios.schemas import UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])

FRONT_URL = os.getenv("FRONT_URL", "http://localhost:5500").rstrip("/")


class LoginIn(BaseModel):
    email: str
    senha: str


class EsqueciSenhaIn(BaseModel):
    email: str = Field(max_length=100)


class RedefinirSenhaIn(BaseModel):
    token: str = Field(min_length=10, max_length=600)
    nova_senha: str = Field(min_length=6, max_length=128)


@router.post("/login", response_model=UsuarioOut)
def login(dados: LoginIn, conn=Depends(get_conn)):
    # TODO(back): emitir JWT e proteger as demais rotas com Depends(usuario_atual)
    usuario = usuarios_repo.buscar_por_email(conn, dados.email)
    if not usuario or not verificar_senha(dados.senha, usuario["senha_hash"]):
        raise HTTPException(401, "E-mail ou senha inválidos")
    return usuario


@router.post("/esqueci-senha")
def esqueci_senha(dados: EsqueciSenhaIn, tarefas: BackgroundTasks, conn=Depends(get_conn)):
    """Pede o link de redefinição. A resposta é sempre a mesma, exista o e-mail ou não (não revela quem tem conta)."""
    usuario = usuarios_repo.buscar_por_email(conn, dados.email.strip())
    if usuario:
        token = reset_token.gerar(usuario["id_usuario"], usuario["senha_hash"])
        link = f"{FRONT_URL}/esqueciSenha.html?token={token}"
        tarefas.add_task(enviar_link_recuperacao, usuario["email"], link)
    return {"detail": "Se o e-mail estiver cadastrado, enviamos um link para redefinir a senha."}


@router.post("/redefinir-senha")
def redefinir_senha(dados: RedefinirSenhaIn, conn=Depends(get_conn)):
    """Troca a senha usando o token do link. Cada link vale uma vez e expira (padrão: 30 min)."""
    invalido = HTTPException(400, "Link inválido ou expirado. Peça um novo.")
    info = reset_token.ler(dados.token)
    if not info:
        raise invalido
    atual = usuarios_repo.buscar_hash(conn, info["u"])
    if not atual or reset_token.impressao(atual["senha_hash"]) != info["f"]:
        raise invalido  # usuário removido ou senha já trocada (link já usado)
    usuarios_repo.atualizar_senha(conn, info["u"], hash_senha(dados.nova_senha))
    return {"detail": "Senha alterada. Entre com a nova senha."}
