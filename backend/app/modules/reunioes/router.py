from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from .schemas import ReuniaoOut, ReuniaoCreate, ReuniaoUpdate
from . import repository as repo
from app.core.database import get_conn
from datetime import datetime
from .services import email_service
from psycopg.errors import ForeignKeyViolation

router = APIRouter(prefix="/reunioes", tags=["reunioes"])

def _validar(conn, d: dict, ignorar_id: int | None = None):
    if repo.existe_conflito(conn, d["id_sala"], d["data_inicio"], d["data_fim"], ignorar_id):
        raise HTTPException(409, "A sala já está reservada nesse horário")

@router.get("/", response_model=list[ReuniaoOut])
def listar(id_sala: int | None = None, conn=Depends(get_conn)):
    return repo.listar(conn, id_sala)

@router.get("/{id_reuniao}", response_model=ReuniaoOut)
def buscar(id_reuniao: int, conn=Depends(get_conn)):
    reuniao = repo.buscar(conn, id_reuniao)
    if not reuniao:
        raise HTTPException(404, "Reunião não encontrada")
    return reuniao

@router.post("/", response_model=ReuniaoOut, status_code=201)
def criar(dados: ReuniaoCreate, conn=Depends(get_conn)):
    d = dados.model_dump()
    _validar(conn, d)
    try:
       nova = repo.criar(conn, d)
    except ForeignKeyViolation:
        raise HTTPException(400, "Sala não encontrada")

    # MODO TESTE DO EMAIL
    try:
        cur = conn.cursor()
        cur.execute("SELECT email FROM usuarios WHERE id = %s", (d["id_usuario"],))
        row = cur.fetchone()
        email_usuario = row[0] if row else None
        cur.close()
        print(f"DEBUG email encontrado: {email_usuario} | nova: {nova}")
        if isinstance(nova, dict):
            nova["email"] = email_usuario
        email_service.enviar_email_reuniao(nova)
    except Exception as e:
        print(f"Falha ao enviar email (modo teste): {e}")

    return nova

@router.put("/{id_reuniao}", response_model=ReuniaoOut)
def atualizar(id_reuniao: int, dados: ReuniaoUpdate, conn=Depends(get_conn)):
    d = dados.model_dump(exclude_unset=True)

    atual = repo.buscar(conn, id_reuniao)
    if not atual:
        raise HTTPException(404, "Reunião não encontrada")

    merged = {**atual, **d}

    if "data_inicio" in d or "data_fim" in d or "id_sala" in d:
        _validar(conn, merged, ignorar_id=id_reuniao)

    atualizada = repo.atualizar(conn, id_reuniao, merged)
    if not atualizada:
        raise HTTPException(404, "Reunião não encontrada")

    return atualizada

@router.delete("/{id_reuniao}", status_code=204)
def deletar(id_reuniao: int, conn=Depends(get_conn)):
    if not repo.deletar(conn, id_reuniao):
        raise HTTPException(404, "Reunião não encontrada")
    return None