"""Apaga do banco as reuniões e os eventos de dias que já passaram e renova as reuniões fixas.

Regra: uma reunião some quando o DIA em que terminou acaba (hoje às 00:00 no fuso APP_TIMEZONE, padrão
America/Fortaleza, UTC-3). Reunião de hoje, mesmo já encerrada, continua até a virada do dia.
Roda ao iniciar o servidor e depois a cada LIMPEZA_INTERVALO_MIN minutos (padrão 60).
Desligar: LIMPEZA_REUNIOES=0. Apagar é definitivo (reunião, convites e eventos), não há lixeira.
"""
import asyncio
import logging
import os

import psycopg

from app.core.database import DATABASE_URL
from app.core.tempo import inicio_de_hoje  # noqa: F401  (reexportado)
from app.modules.eventos import repository as eventos_repo
from app.modules.reunioes import repository as repo
from app.modules.reunioes_fixas import service as fixas_service

log = logging.getLogger("agendash")

INTERVALO_MIN = int(os.getenv("LIMPEZA_INTERVALO_MIN", "60"))
ATIVA = os.getenv("LIMPEZA_REUNIOES", "1") != "0"


def executar_limpeza() -> int:
    """Uma passada: apaga reuniões e eventos de dias anteriores e renova as reuniões fixas.
    Conexão própria (commit no fim). Nunca levanta: erro vai para o log."""
    apagadas = 0
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=30) as conn:
            limite = inicio_de_hoje()
            reunioes = repo.apagar_passadas(conn, limite)
            eventos = eventos_repo.apagar_passados(conn, limite)
        apagadas = reunioes + eventos
        if apagadas:
            log.info("Limpeza: %d reunião(ões) e %d evento(s) de dias anteriores apagado(s).", reunioes, eventos)
    except Exception:
        log.exception("Falha na limpeza de reuniões antigas (tenta de novo no próximo ciclo)")
    try:  # separado: se a tabela de fixas ainda não existir, a limpeza acima não é prejudicada
        with psycopg.connect(DATABASE_URL, connect_timeout=30) as conn:
            novas = fixas_service.renovar_todas(conn, inicio_de_hoje().date())
        if novas:
            log.info("Reuniões fixas: %d reunião(ões) criada(s) para os próximos dias.", novas)
    except Exception:
        log.exception("Falha ao renovar reuniões fixas")
    return apagadas


async def ciclo_de_limpeza() -> None:
    while True:
        await asyncio.to_thread(executar_limpeza)
        await asyncio.sleep(INTERVALO_MIN * 60)
