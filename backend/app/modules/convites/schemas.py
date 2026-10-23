from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Status = Literal["pendente", "aceito", "recusado"]


class ConviteCreate(BaseModel):
    id_reuniao: int
    id_usuario: int


class ConviteResposta(BaseModel):
    status_resposta: Status


class ConviteOut(BaseModel):
    id_reuniao: int
    id_usuario: int
    status_resposta: str | None
    data_hora: datetime | None
