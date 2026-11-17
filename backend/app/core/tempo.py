"""Fuso e regra de "dia que já passou". As colunas data_* do banco guardam horário local SEM fuso."""
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException


def fuso():
    try:
        return ZoneInfo(os.getenv("APP_TIMEZONE", "America/Fortaleza"))
    except ZoneInfoNotFoundError:  # sem o pacote tzdata (Windows): o Brasil não tem horário de verão
        return timezone(timedelta(hours=-3))


def inicio_de_hoje(agora: datetime | None = None) -> datetime:
    """Hoje às 00:00, sem fuso."""
    agora = agora or datetime.now(fuso())
    return agora.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


def exigir_nao_passado(inicio: datetime) -> None:
    """Reuniões e eventos são para o futuro: recusa qualquer início em um dia anterior ao de hoje."""
    local = inicio.astimezone(fuso()).replace(tzinfo=None) if inicio.tzinfo else inicio
    if local < inicio_de_hoje():
        raise HTTPException(422, "Não é possível agendar em um dia que já passou.")
