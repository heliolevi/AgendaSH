from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.core.auth import usuario_atual
from app.core.database import get_conn
from app.modules.convites import repository as repo
from app.modules.convites.schemas import ConviteCreate, ConviteOut, ConviteResposta
from app.modules.reunioes import repository as reunioes_repo

router = APIRouter(prefix="/convites", tags=["convites"])


def _organiza(conn, id_reuniao: int, usuario: dict) -> bool:
    """True se o usuário é admin ou o organizador da reunião."""
    if usuario["papel"] == "admin":
        return True
    reuniao = reunioes_repo.buscar(conn, id_reuniao)
    return bool(reuniao) and reuniao["id_usuario"] == usuario["id_usuario"]


@router.get("", response_model=list[ConviteOut])
def listar(id_reuniao: int | None = None, id_usuario: int | None = None,
           conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    # Não-admin só enxerga os próprios convites — ou todos os de uma reunião que organiza.
    if usuario["papel"] != "admin" and not (id_reuniao is not None and _organiza(conn, id_reuniao, usuario)):
        id_usuario = usuario["id_usuario"]
    return repo.listar(conn, id_reuniao, id_usuario)


@router.post("", response_model=ConviteOut, status_code=201)
def criar(dados: ConviteCreate, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    if not _organiza(conn, dados.id_reuniao, usuario):
        raise HTTPException(403, "Só o organizador da reunião pode convidar participantes.")
    try:
        return repo.criar(conn, dados.id_reuniao, dados.id_usuario)
    except UniqueViolation:
        raise HTTPException(409, "Usuário já convidado para essa reunião")
    except ForeignKeyViolation:
        raise HTTPException(400, "Reunião ou usuário inexistente")


@router.put("/{id_reuniao}/{id_usuario}", response_model=ConviteOut)
def responder(id_reuniao: int, id_usuario: int, dados: ConviteResposta,
              conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    # Só o próprio convidado (ou admin) responde ao convite.
    if usuario["papel"] != "admin" and id_usuario != usuario["id_usuario"]:
        raise HTTPException(403, "Você só pode responder aos seus próprios convites.")
    convite = repo.responder(conn, id_reuniao, id_usuario, dados.status_resposta)
    if not convite:
        raise HTTPException(404, "Convite não encontrado")
    return convite


@router.delete("/{id_reuniao}/{id_usuario}", status_code=204)
def remover(id_reuniao: int, id_usuario: int, conn=Depends(get_conn), usuario=Depends(usuario_atual)):
    # O organizador da reunião, o próprio convidado ou um admin podem remover o convite.
    if not (_organiza(conn, id_reuniao, usuario) or id_usuario == usuario["id_usuario"]):
        raise HTTPException(403, "Sem permissão para remover este convite.")
    if not repo.remover(conn, id_reuniao, id_usuario):
        raise HTTPException(404, "Convite não encontrado")
