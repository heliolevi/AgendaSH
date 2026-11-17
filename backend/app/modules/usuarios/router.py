from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.core.auth import somente_admin, usuario_atual
from app.core.database import get_conn
from app.core.security import hash_senha
from app.modules.usuarios import repository as repo
from app.modules.usuarios.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.modules.verificacao import service as codigos

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def _exigir_dono_ou_admin(usuario: dict, id_alvo: int) -> None:
    if usuario["papel"] != "admin" and usuario["id_usuario"] != id_alvo:
        raise HTTPException(403, "Voce so pode acessar o seu proprio perfil.")


@router.get("", response_model=list[UsuarioOut])
def listar(conn=Depends(get_conn), _admin=Depends(somente_admin)):
    # Listar todos os usuarios e informacao de administracao.
    return repo.listar(conn)


@router.get("/{id_usuario}", response_model=UsuarioOut)
def buscar(id_usuario: int, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    _exigir_dono_ou_admin(usuario, id_usuario)
    encontrado = repo.buscar(conn, id_usuario)
    if not encontrado:
        raise HTTPException(404, "Usuario nao encontrado")
    return encontrado


@router.post("", response_model=UsuarioOut, status_code=201)
def criar(dados: UsuarioCreate, conn=Depends(get_conn)):
    # Rota publica (cadastro): so cria a conta quem provou ter o e-mail (codigo enviado por SMTP).
    codigos.validar(conn, dados.email, "cadastro", dados.codigo)
    try:
        return repo.criar(conn, dados.nome, dados.email, hash_senha(dados.senha))
    except UniqueViolation:
        raise HTTPException(409, "E-mail ja cadastrado")


@router.put("/{id_usuario}", response_model=UsuarioOut)
def atualizar(id_usuario: int, dados: UsuarioUpdate, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    _exigir_dono_ou_admin(usuario, id_usuario)
    try:
        atualizado = repo.atualizar(conn, id_usuario, dados.nome, dados.email)
    except UniqueViolation:
        raise HTTPException(409, "E-mail ja cadastrado")
    if not atualizado:
        raise HTTPException(404, "Usuario nao encontrado")
    return atualizado


@router.delete("/{id_usuario}", status_code=204)
def remover(id_usuario: int, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    _exigir_dono_ou_admin(usuario, id_usuario)
    try:
        ok = repo.remover(conn, id_usuario)
    except ForeignKeyViolation:
        raise HTTPException(409, "Usuario possui reunioes ou convites vinculados")
    if not ok:
        raise HTTPException(404, "Usuario nao encontrado")
