"""Recuperação de senha e login com hash inválido. Não usa banco: o repositório é substituído."""
import pytest
from fastapi.testclient import TestClient

from app.core import reset_token
from app.core.database import get_conn
from app.core.security import hash_senha, verificar_senha
from app.main import app
from app.modules.auth import router as auth_router


class Banco:
    """Um 'usuário' em memória, com as funções do repositório que a rota usa."""

    def __init__(self, senha="antiga123"):
        self.user = {"id_usuario": 7, "nome": "Ana", "email": "ana@undb.edu.br", "criado_em": "2026-01-01T00:00:00",
                     "senha_hash": hash_senha(senha)}

    def buscar_por_email(self, conn, email):
        return self.user if email.lower() == self.user["email"] else None

    def buscar_hash(self, conn, id_usuario):
        return self.user if id_usuario == self.user["id_usuario"] else None

    def atualizar_senha(self, conn, id_usuario, senha_hash):
        self.user["senha_hash"] = senha_hash
        return True


@pytest.fixture
def ctx(monkeypatch):
    banco = Banco()
    enviados = []
    for nome in ("buscar_por_email", "buscar_hash", "atualizar_senha"):
        monkeypatch.setattr(auth_router.usuarios_repo, nome, getattr(banco, nome))
    monkeypatch.setattr(auth_router, "enviar_link_recuperacao", lambda destino, link: enviados.append((destino, link)))
    app.dependency_overrides[get_conn] = lambda: iter([object()])
    yield TestClient(app, raise_server_exceptions=False), banco, enviados
    app.dependency_overrides.clear()


def _token_do_link(link):
    return link.split("token=", 1)[1]


def test_email_cadastrado_recebe_link_e_resposta_e_generica(ctx):
    client, _, enviados = ctx
    r = client.post("/auth/esqueci-senha", json={"email": "ANA@undb.edu.br"})
    assert r.status_code == 200
    assert len(enviados) == 1 and enviados[0][0] == "ana@undb.edu.br"
    assert "esqueciSenha.html?token=" in enviados[0][1]


def test_email_inexistente_responde_igual_e_nao_envia(ctx):
    client, _, enviados = ctx
    r_ok = client.post("/auth/esqueci-senha", json={"email": "ana@undb.edu.br"})
    r_no = client.post("/auth/esqueci-senha", json={"email": "ninguem@undb.edu.br"})
    assert r_no.status_code == 200 and r_no.json() == r_ok.json()  # não revela quem tem conta
    assert len(enviados) == 1


def test_fluxo_completo_troca_a_senha_e_login_usa_a_nova(ctx):
    client, banco, enviados = ctx
    client.post("/auth/esqueci-senha", json={"email": "ana@undb.edu.br"})
    token = _token_do_link(enviados[0][1])
    r = client.post("/auth/redefinir-senha", json={"token": token, "nova_senha": "nova12345"})
    assert r.status_code == 200
    assert client.post("/auth/login", json={"email": "ana@undb.edu.br", "senha": "nova12345"}).status_code == 200
    assert client.post("/auth/login", json={"email": "ana@undb.edu.br", "senha": "antiga123"}).status_code == 401


def test_link_so_vale_uma_vez(ctx):
    client, _, enviados = ctx
    client.post("/auth/esqueci-senha", json={"email": "ana@undb.edu.br"})
    token = _token_do_link(enviados[0][1])
    assert client.post("/auth/redefinir-senha", json={"token": token, "nova_senha": "primeira1"}).status_code == 200
    r = client.post("/auth/redefinir-senha", json={"token": token, "nova_senha": "segunda22"})
    assert r.status_code == 400


def test_token_adulterado_ou_expirado_e_recusado(ctx):
    client, banco, _ = ctx
    token = reset_token.gerar(7, banco.user["senha_hash"])
    adulterado = token[:-3] + ("AAA" if not token.endswith("AAA") else "BBB")
    assert client.post("/auth/redefinir-senha", json={"token": adulterado, "nova_senha": "xxxxxx"}).status_code == 400
    velho = reset_token.gerar(7, banco.user["senha_hash"], agora=1_000_000)
    assert client.post("/auth/redefinir-senha", json={"token": velho, "nova_senha": "xxxxxx"}).status_code == 400
    assert client.post("/auth/redefinir-senha", json={"token": "lixo.lixo.lixo", "nova_senha": "xxxxxx"}).status_code == 400


def test_senha_nova_curta_da_422(ctx):
    client, banco, _ = ctx
    token = reset_token.gerar(7, banco.user["senha_hash"])
    assert client.post("/auth/redefinir-senha", json={"token": token, "nova_senha": "123"}).status_code == 422


def test_hash_em_outro_formato_nao_derruba_o_login(ctx):
    client, banco, _ = ctx
    banco.user["senha_hash"] = "$2b$12$abcdefghijklmnopqrstuuAbCdEfGhIjKlMnOpQrStUvWxYz012345"  # bcrypt antigo
    assert verificar_senha("qualquer", banco.user["senha_hash"]) is False
    assert client.post("/auth/login", json={"email": "ana@undb.edu.br", "senha": "qualquer"}).status_code == 401
