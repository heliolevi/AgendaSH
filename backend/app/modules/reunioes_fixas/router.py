from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation

from app.core.auth import usuario_atual
from app.core.database import get_conn
from app.core.tempo import inicio_de_hoje
from app.modules.reunioes_fixas import repository as repo
from app.modules.reunioes_fixas import service
from app.modules.reunioes_fixas.schemas import FixaCreate, FixaCriadaOut, FixaOut

router = APIRouter(prefix="/reunioes-fixas", tags=["reunioes-fixas"])


@router.get("", response_model=list[FixaOut])
def listar(id_usuario: int | None = None, conn=Depends(get_conn)):
    return repo.listar(conn, id_usuario, desde=inicio_de_hoje().date())


@router.post("", response_model=FixaCriadaOut, status_code=201)
def criar(dados: FixaCreate, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    hoje = inicio_de_hoje().date()
    if dados.data_inicio < hoje:
        raise HTTPException(422, "Não é possível agendar em um dia que já passou.")
    d = dados.model_dump()
    d["id_usuario"] = usuario["id_usuario"]  # organizador = usuário logado (nunca vem do corpo)
    try:
        fixa = repo.criar(conn, d)
    except ForeignKeyViolation:
        raise HTTPException(400, "Sala inexistente")
    criadas, ignoradas = service.gerar_ocorrencias(conn, fixa, hoje)
    if criadas == 0 and ignoradas:
        raise HTTPException(409, "A sala já está reservada em todos os horários dessa reunião fixa")  # desfaz tudo
    return {**fixa, "reunioes_criadas": criadas, "datas_ignoradas": ignoradas}


@router.delete("/{id_fixa}", status_code=204)
def remover(id_fixa: int, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    """Cancela a série: apaga a reunião fixa e as reuniões dela de hoje em diante."""
    fixa = repo.buscar(conn, id_fixa)
    if not fixa:
        raise HTTPException(404, "Reunião fixa não encontrada")
    if usuario["papel"] != "admin" and fixa["id_usuario"] != usuario["id_usuario"]:
        raise HTTPException(403, "Você só pode cancelar as séries que organiza.")
    if not repo.remover(conn, id_fixa, inicio_de_hoje()):
        raise HTTPException(404, "Reunião fixa não encontrada")
