"""Regra de e-mail da UNDB: aceita só aluno (002-02...@aluno.undb.edu.br) e professor (...@undb.edu.br)."""
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_conn
from app.core.email_policy import validar_email_undb
from app.main import app


@pytest.mark.parametrize("email,tipo", [
    ("002-021234@aluno.undb.edu.br", "aluno"),
    ("002-02123456@aluno.undb.edu.br", "aluno"),
    ("  002-02999@ALUNO.UNDB.EDU.BR ", "aluno"),      # normaliza espaços e maiúsculas
    ("maria.silva@undb.edu.br", "professor"),
    ("prof_joao-2@undb.edu.br", "professor"),
    ("Joao@UNDB.edu.br", "professor"),
])
def test_aceita(email, tipo):
    normal, t = validar_email_undb(email)
    assert t == tipo and normal == normal.lower() and normal == normal.strip()


@pytest.mark.parametrize("email", [
    # provedores gratuitos
    "ana@gmail.com", "ana@outlook.com", "ana@hotmail.com", "ana@yahoo.com", "ana@icloud.com", "ana@live.com",
    "002-021234@gmail.com", "maria.silva@gmail.com",
    # golpes de domínio
    "002-021234@aluno.undb.edu.br.golpe.net", "ana@undb.edu.br.golpe.net", "ana@xundb.edu.br",
    "ana@undb-edu.br", "ana@undb.edu.br.com", "ana@evil.undb.edu.br", "ana@undb.com.br", "ana@undb.edu",
    "ana@undb.edu.br.", "ana@.undb.edu.br", "ana@aluno.undb.edu.br.evil.com",
    # letras parecidas / punycode
    "ana@undb.edu.br".replace("u", "\u0443"), "ana@xn--undb-edu.br", "ana@undb.edu.br".replace("a", "\u0430", 1),
    "ana@xn--undb.edu.br",
    # truques de formato
    "ana@undb.edu.br,hacker@gmail.com", "ana@undb.edu.br;hacker@gmail.com", "ana@gmail.com@undb.edu.br",
    "undb.edu.br@gmail.com", "ana@undb.edu.br\nBcc: x@gmail.com", "ana @undb.edu.br", "<ana@undb.edu.br>",
    '"ana@gmail.com"@undb.edu.br', "ana+tag@undb.edu.br", "ana..silva@undb.edu.br", ".ana@undb.edu.br",
    "ana.@undb.edu.br", "@undb.edu.br", "ana@", "ana", "", "   ", "ana@undb.edu.br'--",
    # aluno com matrícula errada ou domínio trocado
    "001-021234@aluno.undb.edu.br", "002-01234@aluno.undb.edu.br", "002-02@aluno.undb.edu.br",
    "002-02abc@aluno.undb.edu.br", "joao@aluno.undb.edu.br", "002-0212345678901@aluno.undb.edu.br",
    # matrícula de aluno no domínio de professor / local de professor começando com número
    "002-021234@undb.edu.br", "1ana@undb.edu.br",
    # tamanho
    ("a" * 95) + "@undb.edu.br",
])
def test_recusa(email):
    with pytest.raises(ValueError):
        validar_email_undb(email)


def test_nao_aceita_tipo_errado():
    with pytest.raises(ValueError):
        validar_email_undb(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validar_email_undb(123)  # type: ignore[arg-type]


def test_configuravel_por_ambiente(monkeypatch):
    monkeypatch.setenv("EMAIL_DOMINIOS_PROFESSOR", "undb.edu.br,prof.undb.edu.br")
    assert validar_email_undb("x@prof.undb.edu.br")[1] == "professor"
    monkeypatch.setenv("EMAIL_PREFIXO_ALUNO", "002-05")
    assert validar_email_undb("002-05123@aluno.undb.edu.br")[1] == "aluno"
    with pytest.raises(ValueError):
        validar_email_undb("002-02123@aluno.undb.edu.br")


# ---- integração com a API (sem banco) ----
@pytest.fixture
def client():
    app.dependency_overrides[get_conn] = lambda: iter([None])
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_cadastro_com_gmail_recusado_422(client):
    r = client.post("/usuarios", json={"nome": "Ana", "email": "ana@gmail.com", "senha": "12345678"})
    assert r.status_code == 422
    assert "UNDB" in r.json()["detail"] and r.json()["codigo"] == "DADOS_INVALIDOS"


def test_cadastro_com_dominio_golpe_recusado_422(client):
    r = client.post("/usuarios", json={"nome": "Ana", "email": "ana@undb.edu.br.golpe.net", "senha": "12345678"})
    assert r.status_code == 422


def test_troca_de_email_no_perfil_tambem_valida(client):
    r = client.put("/usuarios/1", json={"email": "ana@outlook.com"})
    assert r.status_code == 422


def test_cabecalhos_de_seguranca_reforcados(client):
    r = client.get("/health")
    assert r.headers["content-security-policy"].startswith("default-src 'none'")
    assert r.headers["permissions-policy"] and r.headers["cross-origin-resource-policy"] == "same-site"
    assert "strict-transport-security" not in r.headers  # só em https
    r = client.get("/health", headers={"x-forwarded-proto": "https"})
    assert "max-age=31536000" in r.headers["strict-transport-security"]
