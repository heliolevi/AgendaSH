from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation

from app.core.agenda import sala_ocupada
from app.core.auth import usuario_atual
from app.core.database import get_conn
from app.core.tempo import exigir_nao_passado
from app.modules.reunioes import repository as repo
from app.modules.reunioes.schemas import ReuniaoCreate, ReuniaoOut

router = APIRouter(prefix="/reunioes", tags=["reunioes"])


def _validar(conn, d: dict, ignorar_id: int | None = None):
    exigir_nao_passado(d["data_inicio"])
    if sala_ocupada(conn, d["id_sala"], d["data_inicio"], d["data_fim"], "reuniao" if ignorar_id else None, ignorar_id):
        raise HTTPException(409, "A sala já está reservada nesse horário")


def _exigir_dono(conn, id_reuniao: int, usuario: dict) -> dict:
    """A reunião precisa existir e o usuário ser o organizador (ou admin). Devolve a reunião atual."""
    reuniao = repo.buscar(conn, id_reuniao)
    if not reuniao:
        raise HTTPException(404, "Reunião não encontrada")
    if usuario["papel"] != "admin" and reuniao["id_usuario"] != usuario["id_usuario"]:
        raise HTTPException(403, "Você só pode alterar as reuniões que organiza.")
    return reuniao


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
def criar(dados: ReuniaoCreate, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    d = dados.model_dump()
    d["id_usuario"] = usuario["id_usuario"]  # organizador = usuário logado (nunca vem do corpo)
    _validar(conn, d)
    try:
        return repo.criar(conn, d)
    except ForeignKeyViolation:
        raise HTTPException(400, "Sala inexistente")


@router.put("/{id_reuniao}", response_model=ReuniaoOut)
def atualizar(id_reuniao: int, dados: ReuniaoCreate, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    atual = _exigir_dono(conn, id_reuniao, usuario)
    d = dados.model_dump()
    d["id_usuario"] = atual["id_usuario"]  # preserva o organizador; não dá para transferir pelo corpo
    _validar(conn, d, ignorar_id=id_reuniao)
    try:
        reuniao = repo.atualizar(conn, id_reuniao, d)
    except ForeignKeyViolation:
        raise HTTPException(400, "Sala inexistente")
    if not reuniao:
        raise HTTPException(404, "Reunião não encontrada")
    return reuniao


@router.delete("/{id_reuniao}", status_code=204)
def remover(id_reuniao: int, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    _exigir_dono(conn, id_reuniao, usuario)
    if not repo.remover(conn, id_reuniao):
        raise HTTPException(404, "Reunião não encontrada")
