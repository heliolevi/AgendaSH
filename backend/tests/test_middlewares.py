"""Garantem que erros viram JSON padronizado, com CORS, sem vazar detalhes internos.
Rodar: cd backend && python -m pytest -q   (não precisa de banco: get_conn é substituído)"""
import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import errors as pgerr

from app.core.database import get_conn
from app.main import app

ORIGEM = {"Origin": "http://localhost:5500"}


@pytest.fixture
def client():
    c = TestClient(app, raise_server_exceptions=False)
    yield c
    app.dependency_overrides.clear()


def _conn_que_falha(exc):
    def dep():
        raise exc
        yield  # noqa: pragma generator
    return dep


def test_health_tem_cabecalhos_de_seguranca_e_request_id(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers["x-request-id"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"


def test_banco_fora_do_ar_vira_503_com_cors(client):
    app.dependency_overrides[get_conn] = _conn_que_falha(psycopg.OperationalError("connection refused host=secreto"))
    r = client.get("/usuarios", headers=ORIGEM)
    assert r.status_code == 503
    assert r.json()["codigo"] == "BANCO_INDISPONIVEL"
    assert "secreto" not in r.text  # nada interno vaza
    assert r.headers["access-control-allow-origin"] == ORIGEM["Origin"]  # evita o "NetworkError" no navegador


def test_erro_inesperado_vira_500_generico_com_cors(client):
    app.dependency_overrides[get_conn] = _conn_que_falha(RuntimeError("senha=abc123"))
    r = client.get("/salas", headers=ORIGEM)
    assert r.status_code == 500
    corpo = r.json()
    assert corpo["codigo"] == "ERRO_INTERNO"
    assert "abc123" not in r.text and "Traceback" not in r.text
    assert corpo["request_id"] == r.headers["x-request-id"]
    assert r.headers["access-control-allow-origin"] == ORIGEM["Origin"]


@pytest.mark.parametrize("exc,status,codigo", [
    (pgerr.UniqueViolation("x"), 409, "REGISTRO_DUPLICADO"),
    (pgerr.ForeignKeyViolation("x"), 409, "REFERENCIA_INVALIDA"),
    (pgerr.NotNullViolation("x"), 400, "DADOS_INVALIDOS"),
    (pgerr.CheckViolation("x"), 400, "DADOS_INVALIDOS"),
])
def test_erros_de_banco_mapeados(client, exc, status, codigo):
    app.dependency_overrides[get_conn] = _conn_que_falha(exc)
    r = client.get("/salas")
    assert (r.status_code, r.json()["codigo"]) == (status, codigo)


def test_validacao_422_em_portugues(client):
    app.dependency_overrides[get_conn] = lambda: iter([None])
    r = client.post("/usuarios", json={"nome": "A", "email": "a@a.com", "senha": "123"})
    assert r.status_code == 422
    corpo = r.json()
    assert corpo["codigo"] == "DADOS_INVALIDOS"
    assert "senha" in corpo["detail"] and "curto" in corpo["detail"]
    assert isinstance(corpo["detail"], str)


def test_campo_faltando_422(client):
    app.dependency_overrides[get_conn] = lambda: iter([None])
    r = client.post("/auth/login", json={"email": "a@a.com"})
    assert r.status_code == 422 and "senha: campo obrigatório" in r.json()["detail"]


def test_rota_inexistente_404_padronizado(client):
    r = client.get("/nao-existe")
    assert r.status_code == 404
    assert r.json()["codigo"] == "NAO_ENCONTRADO"


def test_metodo_nao_permitido_405(client):
    r = client.delete("/health")
    assert r.status_code == 405 and r.json()["codigo"] == "METODO_NAO_PERMITIDO"


def test_cors_nao_libera_origem_desconhecida(client):
    r = client.get("/health", headers={"Origin": "http://site-malicioso.com"})
    assert "access-control-allow-origin" not in r.headers


def test_validacao_de_datas_da_reuniao(client):
    app.dependency_overrides[get_conn] = lambda: iter([None])
    r = client.post("/reunioes", json={"id_usuario": 1, "id_sala": 1, "titulo": "x",
                                       "data_inicio": "2026-11-10T10:00:00", "data_fim": "2026-11-10T09:00:00"})
    assert r.status_code == 422 and "data_fim" in r.json()["detail"]
