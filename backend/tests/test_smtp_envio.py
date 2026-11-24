"""Envio real por SMTP contra um servidor local (aiosmtpd): sucesso, login recusado, remetente inválido etc."""
import re
import socket

import pytest
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult, LoginPassword

from app.core import email_sender
from app.core.email_sender import EmailNaoEnviado, enviar_codigo

CHAVES = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "SMTP_TLS", "CODIGO_NO_LOG")


class Caixa:
    def __init__(self):
        self.mensagens = []

    async def handle_DATA(self, server, session, envelope):
        self.mensagens.append(envelope)
        return "250 OK"


def _autenticar(server, session, envelope, mechanism, auth_data):
    ok = isinstance(auth_data, LoginPassword) and auth_data.login == b"usuario" and auth_data.password == b"chave-smtp"
    return AuthResult(success=ok, handled=False)


@pytest.fixture
def smtp(monkeypatch):
    for c in CHAVES:
        monkeypatch.delenv(c, raising=False)
    caixa = Caixa()
    with socket.socket() as t:
        t.bind(("127.0.0.1", 0))
        porta = t.getsockname()[1]
    ctl = Controller(caixa, hostname="127.0.0.1", port=porta, authenticator=_autenticar, auth_required=True, auth_require_tls=False)
    ctl.start()
    monkeypatch.setenv("SMTP_HOST", "127.0.0.1")
    monkeypatch.setenv("SMTP_PORT", str(porta))
    monkeypatch.setenv("SMTP_TLS", "0")
    monkeypatch.setenv("SMTP_USER", "usuario")
    monkeypatch.setenv("SMTP_PASSWORD", "chave-smtp")
    monkeypatch.setenv("SMTP_FROM", "no-reply@agenda.exemplo.com")
    yield caixa
    ctl.stop()


def _msg(caixa):
    assert len(caixa.mensagens) == 1
    return caixa.mensagens[0]


def test_envia_o_codigo_para_o_destinatario(smtp):
    enviar_codigo("002-02123456@aluno.undb.edu.br", "123456", "cadastro", 10)
    m = _msg(smtp)
    assert m.rcpt_tos == ["002-02123456@aluno.undb.edu.br"] and m.mail_from == "no-reply@agenda.exemplo.com"
    corpo = m.content.decode("utf-8", "replace")
    assert re.search(r"\b123456\b", corpo) and "criar sua conta" in corpo and "10 minutos" in corpo


def test_codigo_de_senha_tem_assunto_proprio(smtp):
    enviar_codigo("a@aluno.undb.edu.br", "654321", "senha", 10)
    assert "redefinir" in _msg(smtp).content.decode("utf-8", "replace").lower()


def test_valores_do_env_com_aspas_e_espacos_funcionam(smtp, monkeypatch):
    monkeypatch.setenv("SMTP_USER", ' "usuario" ')
    monkeypatch.setenv("SMTP_PASSWORD", "'chave-smtp'")
    monkeypatch.setenv("SMTP_HOST", " 127.0.0.1 ")
    enviar_codigo("a@aluno.undb.edu.br", "111111", "cadastro", 10)
    assert len(smtp.mensagens) == 1


def test_login_recusado_da_erro_generico_e_log_explica(smtp, monkeypatch, caplog):
    monkeypatch.setenv("SMTP_PASSWORD", "errada")
    with pytest.raises(EmailNaoEnviado) as e:
        enviar_codigo("a@aluno.undb.edu.br", "123456", "cadastro", 10)
    assert "agora" in e.value.publico and "errada" not in e.value.publico
    assert "recusou o login" in caplog.text and "errada" not in caplog.text and not smtp.mensagens


def test_sem_remetente_valido_da_erro_claro(smtp, monkeypatch, caplog):
    monkeypatch.delenv("SMTP_FROM")  # SMTP_USER ("usuario") não é e-mail
    with pytest.raises(EmailNaoEnviado):
        enviar_codigo("a@aluno.undb.edu.br", "123456", "cadastro", 10)
    assert "SMTP_FROM" in caplog.text


def test_brevo_sem_from_verificado_e_explicado(monkeypatch, caplog):
    for c in CHAVES:
        monkeypatch.delenv(c, raising=False)
    monkeypatch.setenv("SMTP_HOST", "smtp-relay.brevo.com")
    monkeypatch.setenv("SMTP_USER", "abc123@smtp-brevo.com")
    with pytest.raises(EmailNaoEnviado):
        enviar_codigo("a@aluno.undb.edu.br", "123456", "cadastro", 10)
    assert "remetente verificado" in caplog.text


def test_porta_invalida_nao_vira_500(smtp, monkeypatch, caplog):
    monkeypatch.setenv("SMTP_PORT", "abc")
    with pytest.raises(EmailNaoEnviado):
        enviar_codigo("a@aluno.undb.edu.br", "123456", "cadastro", 10)
    assert "SMTP_PORT" in caplog.text


def test_servidor_fora_do_ar_da_erro_e_nao_trava(smtp, monkeypatch, caplog):
    monkeypatch.setenv("SMTP_PORT", "1")  # ninguém escuta
    with pytest.raises(EmailNaoEnviado):
        enviar_codigo("a@aluno.undb.edu.br", "123456", "cadastro", 10)
    assert "não foi possível falar" in caplog.text


def test_sem_host_continua_dando_503_e_modo_dev_escreve_no_log(monkeypatch, caplog):
    for c in CHAVES:
        monkeypatch.delenv(c, raising=False)
    with pytest.raises(EmailNaoEnviado):
        enviar_codigo("a@aluno.undb.edu.br", "123456", "cadastro", 10)
    monkeypatch.setenv("CODIGO_NO_LOG", "1")
    enviar_codigo("a@aluno.undb.edu.br", "123456", "cadastro", 10)
    assert "123456" in caplog.text
    assert not email_sender.smtp_configurado()
