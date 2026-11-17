from datetime import date, datetime, time

from pydantic import BaseModel, Field, model_validator


class FixaCreate(BaseModel):
    id_sala: int
    titulo: str = Field(min_length=1, max_length=200)
    descricao: str | None = None
    dia_semana: int = Field(ge=0, le=6, description="0 = segunda ... 6 = domingo")
    hora_inicio: time
    hora_fim: time
    data_inicio: date  # a série começa na primeira data deste dia da semana a partir daqui
    data_fim: date | None = None  # vazio = sem data para acabar

    @model_validator(mode="after")
    def validar(self):
        if self.hora_fim <= self.hora_inicio:
            raise ValueError("hora_fim deve ser posterior a hora_inicio")
        if self.data_fim and self.data_fim < self.data_inicio:
            raise ValueError("data_fim deve ser igual ou posterior a data_inicio")
        return self


class FixaOut(BaseModel):
    id_fixa: int
    id_usuario: int | None
    id_sala: int | None
    titulo: str
    descricao: str | None
    dia_semana: int
    hora_inicio: time
    hora_fim: time
    data_inicio: date
    data_fim: date | None
    criado_em: datetime | None = None


class FixaCriadaOut(FixaOut):
    reunioes_criadas: int
    datas_ignoradas: list[date]  # ocorrências que não couberam porque a sala já estava ocupada
