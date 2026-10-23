from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation

from app.core.database import get_conn
from app.modules.salas import repository as repo
from app.modules.salas.schemas import SalaCreate, SalaOut

router = APIRouter(prefix="/salas", tags=["salas"])


@router.get("", response_model=list[SalaOut])
def listar(conn=Depends(get_conn)):
    return repo.listar(conn)


@router.get("/{id_sala}", response_model=SalaOut)
def buscar(id_sala: int, conn=Depends(get_conn)):
    sala = repo.buscar(conn, id_sala)
    if not sala:
        raise HTTPException(404, "Sala não encontrada")
    return sala


@router.post("", response_model=SalaOut, status_code=201)
def criar(dados: SalaCreate, conn=Depends(get_conn)):
    return repo.criar(conn, dados.model_dump())


@router.put("/{id_sala}", response_model=SalaOut)
def atualizar(id_sala: int, dados: SalaCreate, conn=Depends(get_conn)):
    sala = repo.atualizar(conn, id_sala, dados.model_dump())
    if not sala:
        raise HTTPException(404, "Sala não encontrada")
    return sala


@router.delete("/{id_sala}", status_code=204)
def remover(id_sala: int, conn=Depends(get_conn)):
    try:
        ok = repo.remover(conn, id_sala)
    except ForeignKeyViolation:
        raise HTTPException(409, "Sala possui reuniões vinculadas")
    if not ok:
        raise HTTPException(404, "Sala não encontrada")
