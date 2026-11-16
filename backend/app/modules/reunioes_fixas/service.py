"""Transforma uma reunião fixa (semanal) em reuniões reais dos próximos dias.

As ocorrências são linhas normais de `reuniao` (com id_fixa), então aparecem no calendário, aceitam convite
e entram na checagem de conflito. A limpeza apaga as que passam, e `renovar_todas` cria as seguintes.
"""
import logging
import os
from datetime import date, datetime, timedelta

from app.core.agenda import sala_ocupada
from app.modules.reunioes_fixas import repository as repo

log = logging.getLogger("agendash")

HORIZONTE_DIAS = int(os.getenv("FIXAS_SEMANAS", "8")) * 7


def gerar_ocorrencias(conn, fixa: dict, hoje: date) -> tuple[int, list[date]]:
    """Cria as reuniões da série até HORIZONTE_DIAS à frente. Devolve (criadas, datas que não couberam)."""
    criadas, ignoradas = 0, []
    dia = max(fixa["data_inicio"], hoje)
    ultimo = hoje + timedelta(days=HORIZONTE_DIAS)
    if fixa["data_fim"]:
        ultimo = min(ultimo, fixa["data_fim"])
    while dia <= ultimo:
        if dia.weekday() == fixa["dia_semana"]:
            inicio = datetime.combine(dia, fixa["hora_inicio"])
            fim = datetime.combine(dia, fixa["hora_fim"])
            if not repo.ocorrencia_existe(conn, fixa["id_fixa"], inicio):
                if sala_ocupada(conn, fixa["id_sala"], inicio, fim):
                    ignoradas.append(dia)
                else:
                    repo.criar_ocorrencia(conn, fixa, inicio, fim)
                    criadas += 1
        dia += timedelta(days=1)
    return criadas, ignoradas


def renovar_todas(conn, hoje: date) -> int:
    """Estende todas as séries vigentes até o horizonte. Devolve quantas reuniões novas foram criadas."""
    total = 0
    for fixa in repo.listar(conn, desde=hoje):
        criadas, ignoradas = gerar_ocorrencias(conn, fixa, hoje)
        total += criadas
        if ignoradas:
            log.info("Reunião fixa %s: %d data(s) ignorada(s) por sala ocupada.", fixa["id_fixa"], len(ignoradas))
    return total
