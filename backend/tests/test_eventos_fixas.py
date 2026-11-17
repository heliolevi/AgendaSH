"""Não agendar no passado, eventos e reuniões fixas. Sem banco: repositórios e conflito em memória."""
from datetime import date, datetime, time, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core import tempo
from app.core.auth import usuario_atual
from app.core.database import get_conn
from app.main import app
from app.modules.eventos import repository as eventos_repo
from app.modules.eventos import router as eventos_router
from app.modules.reunioes import repository as reunioes_repo
from app.modules.reunioes import router as reunioes_router
from app.modules.reunioes_fixas import repository as fixas_repo
from app.modules.reunioes_fixas import router as fixas_router
from app.modules.reunioes_fixas import service as fixas_service

HOJE = tempo.inicio_de_hoje()
ONTEM = HOJE - timedelta(days=1)
AMANHA = HOJE + timedelta(days=1)


def _corpo(dia: datetime, extra=None):
    return {"id_usuario": 1, "id_sala": 1, "titulo": "X", "data_inicio": dia.replace(hour=10).isoformat(),
            "data_fim": dia.replace(hour=11).isoformat(), **(extra or {})}


class Conn:
    pass


_USUARIO = {"id_usuario": 1, "papel": "admin", "nome": "Teste", "email": "teste@undb.edu.br"}


@pytest.fixture
def client():
    def conn_falsa():
        yield Conn()

    app.dependency_overrides[get_conn] = conn_falsa
    app.dependency_overrides[usuario_atual] = lambda: _USUARIO
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


# ---------- regra: nada no dia anterior ao atual ----------
def test_exigir_nao_passado_aceita_hoje_e_futuro_e_recusa_ontem():
    tempo.exigir_nao_passado(HOJE.replace(hour=0, minute=1))
    tempo.exigir_nao_passado(AMANHA)
    with pytest.raises(Exception) as e:
        tempo.exigir_nao_passado(ONTEM.replace(hour=23, minute=59))
    assert e.value.status_code == 422


def test_exigir_nao_passado_converte_horario_com_fuso():
    # 02:00 UTC de hoje = 23:00 de ONTEM em UTC-3 => passado
    utc = HOJE.replace(hour=2, tzinfo=timezone.utc)
    with pytest.raises(Exception):
        tempo.exigir_nao_passado(utc)


def test_reuniao_no_dia_anterior_e_recusada(client, monkeypatch):
    r = client.post("/reunioes", json=_corpo(ONTEM))
    assert r.status_code == 422 and "passou" in r.json()["detail"]
    monkeypatch.setattr(reunioes_repo, "buscar", lambda conn, id_reuniao: {"id_usuario": 1, "id_sala": 1})
    assert client.put("/reunioes/1", json=_corpo(ONTEM)).status_code == 422


def test_evento_no_dia_anterior_e_recusado(client):
    assert client.post("/eventos", json=_corpo(ONTEM)).status_code == 422


# ---------- eventos ----------
def test_evento_futuro_e_criado_e_conflito_de_sala_da_409(client, monkeypatch):
    monkeypatch.setattr(eventos_router, "sala_ocupada", lambda *a, **k: False)
    monkeypatch.setattr(eventos_repo, "criar", lambda conn, d: {"id_eventos": 5, **d})
    r = client.post("/eventos", json=_corpo(AMANHA))
    assert r.status_code == 201 and r.json()["id_eventos"] == 5
    monkeypatch.setattr(eventos_router, "sala_ocupada", lambda *a, **k: True)
    assert client.post("/eventos", json=_corpo(AMANHA)).status_code == 409


def test_reuniao_e_evento_disputam_a_mesma_sala(client, monkeypatch):
    """Os dois usam core.agenda.sala_ocupada (consulta reuniao E eventos)."""
    from app.core import agenda
    assert eventos_router.sala_ocupada is agenda.sala_ocupada and reunioes_router.sala_ocupada is agenda.sala_ocupada


def test_evento_fim_antes_do_inicio_da_422(client):
    c = _corpo(AMANHA)
    c["data_fim"] = AMANHA.replace(hour=9).isoformat()
    assert client.post("/eventos", json=c).status_code == 422


# ---------- reuniões fixas ----------
class Repo:
    def __init__(self):
        self.criadas, self.ocupadas = [], set()

    def ocorrencia_existe(self, conn, id_fixa, inicio):
        return any(i == inicio for i, _ in self.criadas)

    def criar_ocorrencia(self, conn, fixa, inicio, fim):
        self.criadas.append((inicio, fim))

    def sala_ocupada(self, conn, sala, inicio, fim, *a, **k):
        return inicio.date() in self.ocupadas


@pytest.fixture
def repo(monkeypatch):
    r = Repo()
    monkeypatch.setattr(fixas_repo, "ocorrencia_existe", r.ocorrencia_existe)
    monkeypatch.setattr(fixas_repo, "criar_ocorrencia", r.criar_ocorrencia)
    monkeypatch.setattr(fixas_service, "sala_ocupada", r.sala_ocupada)
    return r


def _fixa(**kw):
    base = {"id_fixa": 1, "id_usuario": 1, "id_sala": 1, "titulo": "Daily", "descricao": None, "dia_semana": 0,
            "hora_inicio": time(9), "hora_fim": time(10), "data_inicio": date(2026, 11, 16), "data_fim": None}
    return {**base, **kw}


def test_gera_uma_reuniao_por_semana_ate_o_horizonte(repo):
    criadas, ignoradas = fixas_service.gerar_ocorrencias(None, _fixa(), date(2026, 11, 16))  # 16/11/2026 é segunda
    esperado = fixas_service.HORIZONTE_DIAS // 7 + 1
    assert criadas == esperado and not ignoradas
    assert all(i.weekday() == 0 and i.hour == 9 and f.hour == 10 for i, f in repo.criadas)
    assert repo.criadas[1][0] - repo.criadas[0][0] == timedelta(days=7)


def test_respeita_data_fim_e_data_inicio(repo):
    criadas, _ = fixas_service.gerar_ocorrencias(None, _fixa(data_fim=date(2026, 12, 1)), date(2026, 11, 16))
    assert [i.date() for i, _ in repo.criadas] == [date(2026, 11, 16), date(2026, 11, 23), date(2026, 11, 30)]
    assert criadas == 3


def test_nao_cria_no_passado_nem_duplica(repo):
    fixa = _fixa(data_inicio=date(2026, 1, 5))  # série antiga: só vale de hoje em diante
    fixas_service.gerar_ocorrencias(None, fixa, date(2026, 11, 16))
    assert min(i for i, _ in repo.criadas).date() >= date(2026, 11, 16)
    antes = len(repo.criadas)
    assert fixas_service.gerar_ocorrencias(None, fixa, date(2026, 11, 16))[0] == 0  # 2ª rodada: nada novo
    assert len(repo.criadas) == antes


def test_data_com_sala_ocupada_e_ignorada_e_as_outras_sao_criadas(repo):
    repo.ocupadas.add(date(2026, 11, 23))
    criadas, ignoradas = fixas_service.gerar_ocorrencias(None, _fixa(data_fim=date(2026, 12, 1)), date(2026, 11, 16))
    assert ignoradas == [date(2026, 11, 23)] and criadas == 2


def test_post_fixa_no_passado_da_422(client):
    corpo = {"id_usuario": 1, "id_sala": 1, "titulo": "X", "dia_semana": 0, "hora_inicio": "09:00:00",
             "hora_fim": "10:00:00", "data_inicio": (HOJE - timedelta(days=1)).date().isoformat()}
    assert client.post("/reunioes-fixas", json=corpo).status_code == 422


@pytest.mark.parametrize("troca", [{"hora_fim": "08:00:00"}, {"dia_semana": 7}, {"data_fim": "2020-01-01"}])
def test_post_fixa_dados_invalidos_da_422(client, troca):
    corpo = {"id_usuario": 1, "id_sala": 1, "titulo": "X", "dia_semana": 0, "hora_inicio": "09:00:00",
             "hora_fim": "10:00:00", "data_inicio": AMANHA.date().isoformat(), **troca}
    assert client.post("/reunioes-fixas", json=corpo).status_code == 422


def test_post_fixa_com_todas_as_datas_ocupadas_da_409(client, monkeypatch):
    monkeypatch.setattr(fixas_repo, "criar", lambda conn, d: _fixa(**{k: d[k] for k in ("dia_semana", "data_inicio", "data_fim")}))
    monkeypatch.setattr(fixas_router.service, "gerar_ocorrencias", lambda conn, f, h: (0, [h]))
    corpo = {"id_usuario": 1, "id_sala": 1, "titulo": "X", "dia_semana": 0, "hora_inicio": "09:00:00",
             "hora_fim": "10:00:00", "data_inicio": AMANHA.date().isoformat()}
    assert client.post("/reunioes-fixas", json=corpo).status_code == 409


def test_post_fixa_ok_devolve_quantas_foram_criadas_e_as_ignoradas(client, monkeypatch):
    monkeypatch.setattr(fixas_repo, "criar", lambda conn, d: _fixa(**{k: d[k] for k in ("dia_semana", "data_inicio", "data_fim")}))
    monkeypatch.setattr(fixas_router.service, "gerar_ocorrencias", lambda conn, f, h: (7, [date(2026, 12, 7)]))
    corpo = {"id_usuario": 1, "id_sala": 1, "titulo": "X", "dia_semana": 0, "hora_inicio": "09:00:00",
             "hora_fim": "10:00:00", "data_inicio": AMANHA.date().isoformat()}
    r = client.post("/reunioes-fixas", json=corpo)
    assert r.status_code == 201
    assert r.json()["reunioes_criadas"] == 7 and r.json()["datas_ignoradas"] == ["2026-12-07"]


def test_cancelar_fixa_inexistente_da_404(client, monkeypatch):
    monkeypatch.setattr(fixas_repo, "buscar", lambda conn, id_fixa: None)
    assert client.delete("/reunioes-fixas/99").status_code == 404


# ---------- regressão: o SQL de conflito não pode virar NULL quando não há registro a ignorar ----------
def test_sql_de_conflito_tem_guarda_contra_null():
    from app.core.agenda import sala_ocupada

    visto = {}

    class C:
        def execute(self, sql, params):
            visto["sql"], visto["params"] = " ".join(sql.split()), params
            return self

        def fetchone(self):
            return None

    assert sala_ocupada(C(), 1, "2026-11-17T10:00", "2026-11-17T11:00") is False
    # sem guarda `ign IS NULL OR ...`, "NOT (tipo = NULL AND id = NULL)" vira NULL e nenhum conflito é encontrado
    assert "%(ign)s::int IS NULL OR NOT" in visto["sql"]
    assert visto["params"]["ign"] is None and visto["params"]["tipo"] is None
    assert "FROM reuniao" in visto["sql"] and "FROM eventos" in visto["sql"]
