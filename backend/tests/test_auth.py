"""Autenticacao por token: geracao/validacao do JWT, throttle e protecao das rotas.
Nao precisa de banco: as rotas protegidas recusam o acesso ANTES de tocar no banco."""
import pytest
from fastapi.testclient import TestClient

from app.core import auth, throttle
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------- token ----------
def test_token_roundtrip():
    t = auth.criar_token(7, "membro", nome="Ana", email="a@undb.edu.br")
    p = auth.decodificar_token(t)
    assert p["sub"] == "7" and p["papel"] == "membro"


def test_token_adulterado_recusado():
    import base64, json
    cab, _corpo, assin = auth.criar_token(7, "membro").split(".")
    falso = base64.urlsafe_b64encode(
        json.dumps({"sub": "7", "papel": "admin", "exp": 9999999999}).encode()
    ).rstrip(b"=").decode()
    with pytest.raises(Exception):
        auth.decodificar_token(f"{cab}.{falso}.{assin}")


def test_token_expirado_recusado():
    with pytest.raises(Exception):
        auth.decodificar_token(auth.criar_token(1, "membro", expira_min=-1))


# ---------- throttle ----------
def test_throttle_bloqueia_apos_limite():
    chave = "9.9.9.9|brute@undb.edu.br"
    throttle.limpar(chave)
    for _ in range(throttle.MAX_FALHAS):
        assert throttle.segundos_de_bloqueio(chave) == 0
        throttle.registrar_falha(chave)
    assert throttle.segundos_de_bloqueio(chave) > 0
    throttle.limpar(chave)


# ---------- protecao das rotas ----------
def _bearer(papel):
    return {"Authorization": "Bearer " + auth.criar_token(42, papel, nome="T", email="t@undb.edu.br")}


def test_rota_de_negocio_sem_token_401():
    assert client.get("/salas").status_code == 401
    assert client.get("/reunioes").status_code == 401


def test_rota_de_negocio_token_invalido_401():
    assert client.get("/salas", headers={"Authorization": "Bearer x.y.z"}).status_code == 401


def test_admin_sem_token_401():
    assert client.get("/admin/resumo").status_code == 401


def test_admin_com_membro_403():
    assert client.get("/admin/resumo", headers=_bearer("membro")).status_code == 403


def test_cadastro_continua_publico():
    # POST /usuarios sem token nao pode dar 401: e o cadastro. Corpo invalido -> 422 (passou da auth).
    assert client.post("/usuarios", json={}).status_code == 422
