"""Regressão de autorização por objeto (IDOR) e organizador vindo do token.

Sem banco: get_conn e os repositórios são substituídos. O usuário logado é injetado
trocando a dependência usuario_atual.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.auth import usuario_atual
from app.core.database import get_conn
from app.main import app
from app.modules.convites import router as convites_router
from app.modules.reunioes import repository as reunioes_repo


class Conn:
    pass


def _logar(usuario: dict):
    app.dependency_overrides[get_conn] = lambda: iter([Conn()])
    app.dependency_overrides[usuario_atual] = lambda: usuario


@pytest.fixture(autouse=True)
def _limpar():
    yield
    app.dependency_overrides.clear()


MEMBRO = {"id_usuario": 2, "papel": "membro", "nome": "Bia", "email": "bia@undb.edu.br"}
DONO = {"id_usuario": 1, "papel": "membro", "nome": "Ana", "email": "ana@undb.edu.br"}
ADMIN = {"id_usuario": 9, "papel": "admin", "nome": "Adm", "email": "adm@undb.edu.br"}

REUNIAO_DO_1 = {"id_reuniao": 10, "id_usuario": 1, "id_sala": 1}


def _client():
    return TestClient(app, raise_server_exceptions=False)


def test_membro_nao_apaga_reuniao_de_outro(monkeypatch):
    _logar(MEMBRO)
    monkeypatch.setattr(reunioes_repo, "buscar", lambda conn, i: dict(REUNIAO_DO_1))
    r = _client().delete("/reunioes/10")
    assert r.status_code == 403


def test_dono_apaga_a_propria_reuniao(monkeypatch):
    _logar(DONO)
    monkeypatch.setattr(reunioes_repo, "buscar", lambda conn, i: dict(REUNIAO_DO_1))
    monkeypatch.setattr(reunioes_repo, "remover", lambda conn, i: True)
    assert _client().delete("/reunioes/10").status_code == 204


def test_admin_apaga_reuniao_de_qualquer_um(monkeypatch):
    _logar(ADMIN)
    monkeypatch.setattr(reunioes_repo, "buscar", lambda conn, i: dict(REUNIAO_DO_1))
    monkeypatch.setattr(reunioes_repo, "remover", lambda conn, i: True)
    assert _client().delete("/reunioes/10").status_code == 204


def test_apagar_reuniao_inexistente_da_404(monkeypatch):
    _logar(ADMIN)
    monkeypatch.setattr(reunioes_repo, "buscar", lambda conn, i: None)
    assert _client().delete("/reunioes/999").status_code == 404


def test_organizador_vem_do_token_e_ignora_o_corpo(monkeypatch):
    """Mesmo mandando id_usuario=999 no corpo, o organizador gravado é o do token (1)."""
    _logar(DONO)
    monkeypatch.setattr("app.modules.reunioes.router.sala_ocupada", lambda *a, **k: False)
    monkeypatch.setattr(reunioes_repo, "criar", lambda conn, d: {"id_reuniao": 55, **d})
    corpo = {"id_usuario": 999, "id_sala": 1, "titulo": "X",
             "data_inicio": "2090-01-01T10:00:00", "data_fim": "2090-01-01T11:00:00"}
    r = _client().post("/reunioes", json=corpo)
    assert r.status_code == 201
    assert r.json()["id_usuario"] == 1  # token, não 999


def test_responder_convite_de_outro_da_403():
    _logar(MEMBRO)  # id 2 tentando responder pelo usuário 1
    r = _client().put("/convites/10/1", json={"status_resposta": "aceito"})
    assert r.status_code == 403


def test_nao_organizador_nao_convida(monkeypatch):
    _logar(MEMBRO)  # id 2, não é dono da reunião 10 (dono é 1)
    monkeypatch.setattr(convites_router.reunioes_repo, "buscar", lambda conn, i: dict(REUNIAO_DO_1))
    r = _client().post("/convites", json={"id_reuniao": 10, "id_usuario": 3})
    assert r.status_code == 403
