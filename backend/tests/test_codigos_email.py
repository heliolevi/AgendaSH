"""Cadastro e recuperação de senha só com código enviado por e-mail (SMTP). Sem banco: repositórios em memória."""
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_conn
from app.core.email_sender import EmailNaoEnviado, enviar_codigo
from app.core.security import hash_senha
from app.main import app
from app.modules.auth import router as auth_router
from app.modules.usuarios import repository as usuarios_repo
from app.modules.verificacao import repository as verif_repo
from app.modules.verificacao import service


class Verificacoes:
    """Tabela verificacao_email em memória, com relógio que o teste pode avançar."""

    def __init__(self):
        self.linhas, self.agora, self.seq = [], 1000.0, 0

    def segundos_desde_ultimo(self, conn, email, fin):
        t = [r["criado"] for r in self.linhas if (r["email"], r["fin"]) == (email, fin)]
        return None if not t else self.agora - max(t)

    def contar_ultima_hora(self, conn, email, fin):
        return sum(1 for r in self.linhas if (r["email"], r["fin"]) == (email, fin) and self.agora - r["criado"] < 3600)

    def invalidar_anteriores(self, conn, email, fin):
        for r in self.linhas:
            if (r["email"], r["fin"]) == (email, fin):
                r["usado"] = True

    def criar(self, conn, email, fin, codigo_hash, validade_min):
        self.seq += 1
        self.linhas.append({"id_verificacao": self.seq, "email": email, "fin": fin, "codigo_hash": codigo_hash,
                            "expira": self.agora + validade_min * 60, "tentativas": 0, "usado": False, "criado": self.agora})

    def buscar_ativo(self, conn, email, fin):
        ativos = [r for r in self.linhas if (r["email"], r["fin"]) == (email, fin) and not r["usado"] and r["expira"] > self.agora]
        return max(ativos, key=lambda r: r["criado"], default=None)

    def somar_tentativa(self, conn, id_v):
        next(r for r in self.linhas if r["id_verificacao"] == id_v)["tentativas"] += 1

    def marcar_usado(self, conn, id_v):
        next(r for r in self.linhas if r["id_verificacao"] == id_v)["usado"] = True


class Contas:
    def __init__(self):
        self.users = {"ana@undb.edu.br": {"id_usuario": 7, "nome": "Ana", "email": "ana@undb.edu.br",
                                          "criado_em": "2026-01-01T00:00:00", "senha_hash": hash_senha("antiga123")}}

    def buscar_por_email(self, conn, email):
        return self.users.get(email.lower())

    def atualizar_senha(self, conn, id_usuario, senha_hash):
        next(u for u in self.users.values() if u["id_usuario"] == id_usuario)["senha_hash"] = senha_hash
        return True

    def criar(self, conn, nome, email, senha_hash):
        u = {"id_usuario": 99, "nome": nome, "email": email, "criado_em": "2026-01-01T00:00:00", "senha_hash": senha_hash}
        self.users[email] = u
        return u


class Conn:
    def commit(self):
        pass


@pytest.fixture
def ctx(monkeypatch):
    v, contas, enviados = Verificacoes(), Contas(), []
    for nome in ("segundos_desde_ultimo", "contar_ultima_hora", "invalidar_anteriores", "criar", "buscar_ativo",
                 "somar_tentativa", "marcar_usado"):
        monkeypatch.setattr(verif_repo, nome, getattr(v, nome))
    for nome in ("buscar_por_email", "atualizar_senha", "criar"):
        monkeypatch.setattr(usuarios_repo, nome, getattr(contas, nome))
    monkeypatch.setattr(auth_router, "enviar_codigo", lambda dest, cod, fin, min_: enviados.append((dest, cod, fin)))

    def conn_falsa():
        yield Conn()

    app.dependency_overrides[get_conn] = conn_falsa
    yield TestClient(app, raise_server_exceptions=False), v, contas, enviados
    app.dependency_overrides.clear()


NOVO = "joao@undb.edu.br"


def _cadastro(client, codigo, email=NOVO):
    return client.post("/usuarios", json={"nome": "João", "email": email, "senha": "senha123", "codigo": codigo})


# ---------- cadastro ----------
def test_enviar_codigo_recusa_email_fora_da_undb(ctx):
    client, *_ = ctx
    assert client.post("/auth/cadastro/enviar-codigo", json={"email": "joao@gmail.com"}).status_code == 422


def test_enviar_codigo_recusa_email_ja_cadastrado(ctx):
    client, _, _, enviados = ctx
    assert client.post("/auth/cadastro/enviar-codigo", json={"email": "ana@undb.edu.br"}).status_code == 409
    assert enviados == []


def test_cadastro_sem_codigo_ou_com_codigo_errado_nao_cria_conta(ctx):
    client, _, contas, enviados = ctx
    assert client.post("/usuarios", json={"nome": "J", "email": NOVO, "senha": "senha123"}).status_code == 422
    assert _cadastro(client, "123456").status_code == 400  # nunca pediu código
    client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO})
    errado = "000000" if enviados[0][1] != "000000" else "111111"
    assert _cadastro(client, errado).status_code == 400
    assert NOVO not in contas.users


def test_cadastro_com_codigo_certo_cria_conta_e_codigo_so_vale_uma_vez(ctx):
    client, _, contas, enviados = ctx
    r = client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO})
    assert r.status_code == 200 and enviados[0][0] == NOVO and enviados[0][2] == "cadastro"
    codigo = enviados[0][1]
    assert len(codigo) == 6 and codigo.isdigit()
    assert _cadastro(client, codigo).status_code == 201
    assert NOVO in contas.users
    assert _cadastro(client, codigo, email="outro@undb.edu.br").status_code == 400


def test_codigo_de_um_email_nao_vale_para_outro(ctx):
    client, _, contas, enviados = ctx
    client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO})
    assert _cadastro(client, enviados[0][1], email="outro@undb.edu.br").status_code == 400
    assert "outro@undb.edu.br" not in contas.users


def test_codigo_expira(ctx):
    client, v, contas, enviados = ctx
    client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO})
    v.agora += service.VALIDADE_MIN * 60 + 1
    assert _cadastro(client, enviados[0][1]).status_code == 400
    assert NOVO not in contas.users


def test_cinco_erros_invalidam_o_codigo_mesmo_o_certo(ctx):
    client, _, contas, enviados = ctx
    client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO})
    certo = enviados[0][1]
    errado = "000000" if certo != "000000" else "111111"
    for _ in range(service.MAX_TENTATIVAS):
        assert _cadastro(client, errado).status_code == 400
    assert _cadastro(client, certo).status_code == 400
    assert NOVO not in contas.users


def test_limite_de_envios_por_minuto_e_por_hora(ctx):
    client, v, _, enviados = ctx
    assert client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO}).status_code == 200
    assert client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO}).status_code == 429  # logo em seguida
    for _ in range(service.MAX_POR_HORA - 1):
        v.agora += service.INTERVALO_SEG + 1
        assert client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO}).status_code == 200
    v.agora += service.INTERVALO_SEG + 1
    assert client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO}).status_code == 429  # estourou a hora


def test_codigo_novo_invalida_o_anterior(ctx):
    client, v, _, enviados = ctx
    client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO})
    v.agora += service.INTERVALO_SEG + 1
    client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO})
    primeiro, segundo = enviados[0][1], enviados[1][1]
    if primeiro != segundo:
        assert _cadastro(client, primeiro).status_code == 400
    assert _cadastro(client, segundo).status_code == 201


# ---------- sem SMTP ----------
def test_sem_smtp_enviar_codigo_levanta_erro_e_nao_vaza_o_codigo(monkeypatch, caplog):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("CODIGO_NO_LOG", raising=False)
    with pytest.raises(EmailNaoEnviado):
        enviar_codigo("a@undb.edu.br", "654321", "cadastro", 10)
    assert "654321" not in caplog.text


def test_modo_dev_escreve_o_codigo_no_log_so_se_pedido(monkeypatch, caplog):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("CODIGO_NO_LOG", "1")
    enviar_codigo("a@undb.edu.br", "654321", "senha", 10)
    assert "654321" in caplog.text


def test_rota_devolve_503_quando_o_email_nao_sai(ctx, monkeypatch):
    client, *_ = ctx

    def falha(*a, **k):
        raise EmailNaoEnviado("Não foi possível enviar o e-mail agora. Tente novamente em instantes.")

    monkeypatch.setattr(auth_router, "enviar_codigo", falha)
    r = client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO})
    assert r.status_code == 503 and "e-mail" in r.json()["detail"]


# ---------- esqueci a senha ----------
def test_esqueci_senha_resposta_igual_e_so_envia_para_conta_existente(ctx):
    client, _, _, enviados = ctx
    ok = client.post("/auth/esqueci-senha", json={"email": "ANA@undb.edu.br"})
    no = client.post("/auth/esqueci-senha", json={"email": "ninguem@undb.edu.br"})
    assert ok.status_code == no.status_code == 200 and ok.json() == no.json()
    assert [(d, f) for d, _, f in enviados] == [("ana@undb.edu.br", "senha")]


def test_redefinir_senha_com_codigo(ctx):
    client, _, _, enviados = ctx
    client.post("/auth/esqueci-senha", json={"email": "ana@undb.edu.br"})
    codigo = enviados[0][1]
    corpo = {"email": "ana@undb.edu.br", "codigo": codigo, "nova_senha": "nova12345"}
    assert client.post("/auth/redefinir-senha", json=corpo).status_code == 200
    assert client.post("/auth/login", json={"email": "ana@undb.edu.br", "senha": "nova12345"}).status_code == 200
    assert client.post("/auth/login", json={"email": "ana@undb.edu.br", "senha": "antiga123"}).status_code == 401
    assert client.post("/auth/redefinir-senha", json=corpo).status_code == 400  # código já usado


def test_redefinir_senha_com_codigo_errado_ou_de_outra_finalidade(ctx):
    client, _, _, enviados = ctx
    client.post("/auth/esqueci-senha", json={"email": "ana@undb.edu.br"})
    errado = "000000" if enviados[0][1] != "000000" else "111111"
    r = client.post("/auth/redefinir-senha", json={"email": "ana@undb.edu.br", "codigo": errado, "nova_senha": "nova12345"})
    assert r.status_code == 400
    # um código de cadastro não serve para trocar senha
    client.post("/auth/cadastro/enviar-codigo", json={"email": NOVO})
    r = client.post("/auth/redefinir-senha", json={"email": NOVO, "codigo": enviados[-1][1], "nova_senha": "nova12345"})
    assert r.status_code == 400


def test_redefinir_senha_formato_do_codigo_e_senha_curta(ctx):
    client, *_ = ctx
    base = {"email": "ana@undb.edu.br", "codigo": "123456", "nova_senha": "nova12345"}
    assert client.post("/auth/redefinir-senha", json={**base, "codigo": "12ab"}).status_code == 422
    assert client.post("/auth/redefinir-senha", json={**base, "nova_senha": "123"}).status_code == 422
