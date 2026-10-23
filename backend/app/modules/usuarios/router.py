from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.core.database import get_conn
from app.core.security import hash_senha
from app.modules.usuarios import repository as repo
from app.modules.usuarios.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut])
def listar(conn=Depends(get_conn)):
    return repo.listar(conn)


@router.get("/{id_usuario}", response_model=UsuarioOut)
def buscar(id_usuario: int, conn=Depends(get_conn)):
    usuario = repo.buscar(conn, id_usuario)
    if not usuario:
        raise HTTPException(404, "Usuário não encontrado")
    return usuario


@router.post("", response_model=UsuarioOut, status_code=201)
def criar(dados: UsuarioCreate, conn=Depends(get_conn)):
    try:
        return repo.criar(conn, dados.nome, dados.email, hash_senha(dados.senha))
    except UniqueViolation:
        raise HTTPException(409, "E-mail já cadastrado")


@router.put("/{id_usuario}", response_model=UsuarioOut)
def atualizar(id_usuario: int, dados: UsuarioUpdate, conn=Depends(get_conn)):
    try:
        usuario = repo.atualizar(conn, id_usuario, dados.nome, dados.email)
    except UniqueViolation:
        raise HTTPException(409, "E-mail já cadastrado")
    if not usuario:
        raise HTTPException(404, "Usuário não encontrado")
    return usuario


@router.delete("/{id_usuario}", status_code=204)
def remover(id_usuario: int, conn=Depends(get_conn)):
    try:
        ok = repo.remover(conn, id_usuario)
    except ForeignKeyViolation:
        raise HTTPException(409, "Usuário possui reuniões ou convites vinculados")
    if not ok:
        raise HTTPException(404, "Usuário não encontrado")
