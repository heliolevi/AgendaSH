from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation

from app.core.agenda import sala_ocupada
from app.core.auth import usuario_atual
from app.core.database import get_conn
from app.core.tempo import exigir_nao_passado
from app.modules.eventos import repository as repo
from app.modules.eventos.schemas import EventoCreate, EventoOut

router = APIRouter(prefix="/eventos", tags=["eventos"])


def _validar(conn, d: dict, ignorar_id: int | None = None):
    exigir_nao_passado(d["data_inicio"])
    if sala_ocupada(conn, d["id_sala"], d["data_inicio"], d["data_fim"], "evento" if ignorar_id else None, ignorar_id):
        raise HTTPException(409, "A sala já está reservada nesse horário")


def _exigir_dono(conn, id_evento: int, usuario: dict) -> dict:
    """O evento precisa existir e o usuário ser o organizador (ou admin). Devolve o evento atual."""
    evento = repo.buscar(conn, id_evento)
    if not evento:
        raise HTTPException(404, "Evento não encontrado")
    if usuario["papel"] != "admin" and evento["id_usuario"] != usuario["id_usuario"]:
        raise HTTPException(403, "Você só pode alterar os eventos que organiza.")
    return evento


@router.get("", response_model=list[EventoOut])
def listar(id_sala: int | None = None, conn=Depends(get_conn)):
    return repo.listar(conn, id_sala)


@router.get("/{id_evento}", response_model=EventoOut)
def buscar(id_evento: int, conn=Depends(get_conn)):
    evento = repo.buscar(conn, id_evento)
    if not evento:
        raise HTTPException(404, "Evento não encontrado")
    return evento


@router.post("", response_model=EventoOut, status_code=201)
def criar(dados: EventoCreate, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    d = dados.model_dump()
    d["id_usuario"] = usuario["id_usuario"]  # organizador = usuário logado (nunca vem do corpo)
    _validar(conn, d)
    try:
        return repo.criar(conn, d)
    except ForeignKeyViolation:
        raise HTTPException(400, "Sala inexistente")


@router.put("/{id_evento}", response_model=EventoOut)
def atualizar(id_evento: int, dados: EventoCreate, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    atual = _exigir_dono(conn, id_evento, usuario)
    d = dados.model_dump()
    d["id_usuario"] = atual["id_usuario"]  # preserva o organizador
    _validar(conn, d, ignorar_id=id_evento)
    try:
        evento = repo.atualizar(conn, id_evento, d)
    except ForeignKeyViolation:
        raise HTTPException(400, "Sala inexistente")
    if not evento:
        raise HTTPException(404, "Evento não encontrado")
    return evento


@router.delete("/{id_evento}", status_code=204)
def remover(id_evento: int, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    _exigir_dono(conn, id_evento, usuario)
    if not repo.remover(conn, id_evento):
        raise HTTPException(404, "Evento não encontrado")
