"""Envio do e-mail de recuperação de senha.

Com SMTP_HOST definido, envia de verdade (SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_TLS=1).
Sem SMTP_HOST (desenvolvimento), NÃO envia: escreve o link no log do servidor para você copiar.
Nunca deixe o modo sem SMTP em produção: o link no log dá acesso à conta.
"""
import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger("agendash")


def enviar_link_recuperacao(destino: str, link: str) -> None:
    host = os.getenv("SMTP_HOST")
    if not host:
        log.warning("SMTP não configurado (modo dev). Link de recuperação para %s: %s", destino, link)
        return
    msg = EmailMessage()
    msg["Subject"] = "AgendaSH: redefinir sua senha"
    msg["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "no-reply@agendash.local"
    msg["To"] = destino
    msg.set_content(
        "Recebemos um pedido para redefinir sua senha no AgendaSH.\n\n"
        f"Abra o link (vale por poucos minutos e só pode ser usado uma vez):\n{link}\n\n"
        "Se não foi você, ignore este e-mail: sua senha continua a mesma."
    )
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=20) as s:
            if os.getenv("SMTP_TLS", "1") == "1":
                s.starttls()
            if os.getenv("SMTP_USER"):
                s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
            s.send_message(msg)
    except Exception:  # não derruba a requisição nem vaza detalhe; o motivo fica no log
        log.exception("Falha ao enviar e-mail de recuperação para %s", destino)
