"""Reuniões de dias que já passaram são apagadas (com os convites). Sem banco."""
from datetime import datetime, timedelta, timezone

from app.modules.reunioes import limpeza
from app.modules.reunioes import repository as repo


class ConnFalsa:
    def __init__(self, apagadas=2):
        self.sql, self.apagadas = [], apagadas

    def execute(self, sql, params=None):
        self.sql.append((" ".join(sql.split()), params))
        return self

    @property
    def rowcount(self):
        return self.apagadas


def test_limite_e_a_meia_noite_de_hoje_no_horario_local():
    fuso = timezone(timedelta(hours=-3))
    assert limpeza.inicio_de_hoje(datetime(2026, 11, 16, 15, 14, 59, tzinfo=fuso)) == datetime(2026, 11, 16, 0, 0)
    assert limpeza.inicio_de_hoje(datetime(2026, 11, 16, 23, 59, 59, tzinfo=fuso)) == datetime(2026, 11, 16, 0, 0)
    assert limpeza.inicio_de_hoje(datetime(2026, 11, 17, 0, 0, 1, tzinfo=fuso)) == datetime(2026, 11, 17, 0, 0)


def test_apaga_convites_antes_das_reunioes_e_so_as_que_terminaram_antes_do_limite():
    conn, limite = ConnFalsa(apagadas=3), datetime(2026, 11, 16)
    assert repo.apagar_passadas(conn, limite) == 3
    (sql1, p1), (sql2, p2) = conn.sql
    assert sql1.startswith("DELETE FROM convite") and "data_fim < %s" in sql1
    assert sql2 == "DELETE FROM reuniao WHERE data_fim < %s"
    assert p1 == (limite,) and p2 == (limite,)


def test_erro_no_banco_nao_derruba_o_servidor(monkeypatch):
    def quebra(*a, **k):
        raise RuntimeError("banco fora")

    monkeypatch.setattr(limpeza.psycopg, "connect", quebra)
    assert limpeza.executar_limpeza() == 0  # só registra no log
