from pydantic import BaseModel, Field


class SalaBase(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    capacidade: int = Field(gt=0)
    tipo: str = Field(max_length=250)  # ex.: presencial, online
    localizacao_link: str | None = None  # endereço da sala ou link da chamada


class SalaCreate(SalaBase):
    pass


class SalaOut(SalaBase):
    id_sala: int
