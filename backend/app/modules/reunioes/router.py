from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from .schemas import ReuniaoOut, ReuniaoCreate, ReuniaoUpdate
from .repository import repo
from app.core.database import get_conn
from datetime import datetime
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
def criar(dados: ReuniaoCreate, background_tasks: BackgroundTasks, conn=Depends(get_conn)):
    d = dados.model_dump()
    _validar(conn, d)
    try:
        reuniao = repo.criar(conn, d)
        
        # E-mail real em segundo plano
        background_tasks.add_task(
            email_service.send_agendamento_email,
            cliente_email=getattr(reuniao, 'email', 'teste@aluno.com'),
            cliente_nome=getattr(reuniao, 'titulo', 'Cliente'),
            agendamento_id=reuniao.id,
            data_hora=getattr(reuniao, 'data_hora', datetime.now())
        )
        return reuniao
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
