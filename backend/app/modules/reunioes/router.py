from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation

from app.core.database import get_conn
from app.modules.reunioes import repository as repo
from app.modules.reunioes.schemas import ReuniaoCreate, ReuniaoOut

router = APIRouter(prefix="/reunioes", tags=["reunioes"])


def _validar(conn, d: dict, ignorar_id: int | None = None):
    if repo.existe_conflito(conn, d["id_sala"], d["data_inicio"], d["data_fim"], ignorar_id):
        raise HTTPException(409, "A sala já está reservada nesse horário")


@router.get("", response_model=list[ReuniaoOut])
def listar(id_sala: int | None = None, conn=Depends(get_conn)):
    return repo.listar(conn, id_sala)


@router.get("/{id_reuniao}", response_model=ReuniaoOut)
def buscar(id_reuniao: int, conn=Depends(get_conn)):
    reuniao = repo.buscar(conn, id_reuniao)
    if not reuniao:
        raise HTTPException(404, "Reunião não encontrada")
    return reuniao


@router.post("", response_model=ReuniaoOut, status_code=201)
def criar(dados: ReuniaoCreate, conn=Depends(get_conn)):
    d = dados.model_dump()
    _validar(conn, d)
    try:
        return repo.criar(conn, d)
    except ForeignKeyViolation:
        raise HTTPException(400, "Usuário ou sala inexistente")


@router.put("/{id_reuniao}", response_model=ReuniaoOut)
def atualizar(id_reuniao: int, dados: ReuniaoCreate, conn=Depends(get_conn)):
    d = dados.model_dump()
    _validar(conn, d, ignorar_id=id_reuniao)
    try:
        reuniao = repo.atualizar(conn, id_reuniao, d)
    except ForeignKeyViolation:
        raise HTTPException(400, "Usuário ou sala inexistente")
    if not reuniao:
        raise HTTPException(404, "Reunião não encontrada")
    return reuniao


@router.delete("/{id_reuniao}", status_code=204)
def remover(id_reuniao: int, conn=Depends(get_conn)):
    if not repo.remover(conn, id_reuniao):
        raise HTTPException(404, "Reunião não encontrada")
