from fastapi import APIRouter, Depends, HTTPException
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.core.database import get_conn
from app.modules.convites import repository as repo
from app.modules.convites.schemas import ConviteCreate, ConviteOut, ConviteResposta

router = APIRouter(prefix="/convites", tags=["convites"])


@router.get("", response_model=list[ConviteOut])
def listar(id_reuniao: int | None = None, id_usuario: int | None = None, conn=Depends(get_conn)):
    return repo.listar(conn, id_reuniao, id_usuario)


@router.post("", response_model=ConviteOut, status_code=201)
def criar(dados: ConviteCreate, conn=Depends(get_conn)):
    try:
        return repo.criar(conn, dados.id_reuniao, dados.id_usuario)
    except UniqueViolation:
        raise HTTPException(409, "Usuário já convidado para essa reunião")
    except ForeignKeyViolation:
        raise HTTPException(400, "Reunião ou usuário inexistente")


@router.put("/{id_reuniao}/{id_usuario}", response_model=ConviteOut)
def responder(id_reuniao: int, id_usuario: int, dados: ConviteResposta, conn=Depends(get_conn)):
    convite = repo.responder(conn, id_reuniao, id_usuario, dados.status_resposta)
    if not convite:
        raise HTTPException(404, "Convite não encontrado")
    return convite


@router.delete("/{id_reuniao}/{id_usuario}", status_code=204)
def remover(id_reuniao: int, id_usuario: int, conn=Depends(get_conn)):
    if not repo.remover(conn, id_reuniao, id_usuario):
        raise HTTPException(404, "Convite não encontrado")
