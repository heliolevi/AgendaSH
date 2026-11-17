"""Envio do código de verificação por e-mail (SMTP).

Variáveis (.env): SMTP_HOST, SMTP_PORT (587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_TLS (1 = STARTTLS,
ssl = SSL direto na porta 465, 0 = sem criptografia).

Sem SMTP_HOST o envio FALHA (503): o código só existe para quem o recebe por e-mail.
Exceção só para desenvolvimento: CODIGO_NO_LOG=1 escreve o código no log do servidor em vez de enviar.
Nunca ligue CODIGO_NO_LOG em produção: quem lê o log consegue criar conta ou trocar senha.
"""
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

log = logging.getLogger("agendash")

ASSUNTO = {"cadastro": "AgendaSH: código para criar sua conta", "senha": "AgendaSH: código para redefinir sua senha"}
MOTIVO = {"cadastro": "criar sua conta no AgendaSH", "senha": "redefinir sua senha no AgendaSH"}


class EmailNaoEnviado(Exception):
    """SMTP ausente ou com falha. `publico` é a mensagem segura para devolver ao usuário."""

    def __init__(self, publico: str):
        super().__init__(publico)
        self.publico = publico


def smtp_configurado() -> bool:
    return bool(os.getenv("SMTP_HOST"))


def enviar_codigo(destino: str, codigo: str, finalidade: str, validade_min: int) -> None:
    host = os.getenv("SMTP_HOST")
    if not host:
        if os.getenv("CODIGO_NO_LOG") == "1":
            log.warning("[DEV] CODIGO_NO_LOG=1, e-mail NÃO enviado. Código (%s) para %s: %s", finalidade, destino, codigo)
            return
        log.error("SMTP_HOST não configurado: não foi possível enviar o código para %s", destino)
        raise EmailNaoEnviado("O envio de e-mail não está configurado no servidor. Fale com o administrador.")

    msg = EmailMessage()
    msg["Subject"] = ASSUNTO[finalidade]
    msg["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "no-reply@agendash.local"
    msg["To"] = destino
    msg.set_content(
        f"Seu código para {MOTIVO[finalidade]}:\n\n    {codigo}\n\n"
        f"Ele vale por {validade_min} minutos e só pode ser usado uma vez.\n"
        "Se não foi você quem pediu, ignore este e-mail. Ninguém do AgendaSH pede esse código."
    )
    porta = int(os.getenv("SMTP_PORT", "587"))
    modo = os.getenv("SMTP_TLS", "1")
    try:
        if modo == "ssl":
            s = smtplib.SMTP_SSL(host, porta, timeout=20, context=ssl.create_default_context())
        else:
            s = smtplib.SMTP(host, porta, timeout=20)
        with s:
            if modo == "1":
                s.starttls(context=ssl.create_default_context())
            if os.getenv("SMTP_USER"):
                s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
            s.send_message(msg)
    except Exception:  # o motivo fica no log (sem a senha); o usuário recebe mensagem genérica
        log.exception("Falha ao enviar e-mail de código (%s) para %s", finalidade, destino)
        raise EmailNaoEnviado("Não foi possível enviar o e-mail agora. Tente novamente em instantes.") from None
