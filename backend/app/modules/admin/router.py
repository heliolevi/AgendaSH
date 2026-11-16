"""Area administrativa. Todas as rotas exigem papel 'admin' (Depends(somente_admin))."""
from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation
from pydantic import BaseModel, field_validator

from app.core.auth import somente_admin
from app.core.database import get_conn
from app.modules.usuarios import repository as usuarios_repo

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(somente_admin)])

PAPEIS = {"membro", "admin"}


class PapelIn(BaseModel):
    papel: str

    @field_validator("papel")
    @classmethod
    def papel_valido(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in PAPEIS:
            raise ValueError("Papel deve ser 'membro' ou 'admin'.")
        return v


@router.get("/resumo")
def resumo(conn=Depends(get_conn)):
    """Contadores gerais para o painel admin."""
    n = lambda sql: conn.execute(sql).fetchone()["n"]
    return {
        "usuarios": n("SELECT count(*) AS n FROM usuario"),
        "reunioes": n("SELECT count(*) AS n FROM reuniao"),
        "salas": n("SELECT count(*) AS n FROM sala"),
        "convites": n("SELECT count(*) AS n FROM convite"),
    }


@router.get("/usuarios")
def listar_usuarios(conn=Depends(get_conn)):
    return usuarios_repo.listar_com_papel(conn)


@router.patch("/usuarios/{id_usuario}")
def definir_papel(id_usuario: int, dados: PapelIn, admin=Depends(somente_admin), conn=Depends(get_conn)):
    if id_usuario == admin["id_usuario"] and dados.papel != "admin":
        raise HTTPException(400, "Voce nao pode remover o seu proprio acesso de administrador.")
    usuario = usuarios_repo.definir_papel(conn, id_usuario, dados.papel)
    if not usuario:
        raise HTTPException(404, "Usuario nao encontrado")
    return usuario


@router.delete("/usuarios/{id_usuario}", status_code=204)
def remover_usuario(id_usuario: int, admin=Depends(somente_admin), conn=Depends(get_conn)):
    if id_usuario == admin["id_usuario"]:
        raise HTTPException(400, "Voce nao pode excluir a sua propria conta por aqui.")
    try:
        ok = usuarios_repo.remover(conn, id_usuario)
    except ForeignKeyViolation:
        raise HTTPException(409, "Usuario possui reunioes ou convites vinculados")
    if not ok:
        raise HTTPException(404, "Usuario nao encontrado")
