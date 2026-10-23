from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class ReuniaoCreate(BaseModel):
    id_usuario: int  # organizador (TODO: virá do usuário logado)
    id_sala: int
    titulo: str = Field(min_length=1, max_length=200)
    descricao: str | None = None
    data_inicio: datetime
    data_fim: datetime

    @model_validator(mode="after")
    def fim_depois_do_inicio(self):
        if self.data_fim <= self.data_inicio:
            raise ValueError("data_fim deve ser posterior a data_inicio")
        return self


class ReuniaoOut(BaseModel):
    id_reuniao: int
    id_usuario: int | None
    id_sala: int | None
    titulo: str
    descricao: str | None
    data_inicio: datetime
    data_fim: datetime
