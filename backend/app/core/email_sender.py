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


def _env(nome: str, padrao: str = "") -> str:
    """Lê do ambiente tirando espaços e aspas que costumam sobrar ao colar no .env."""
    return (os.getenv(nome) or padrao).strip().strip("\"'").strip()


def smtp_configurado() -> bool:
    return bool(_env("SMTP_HOST"))


def _falha(motivo: str) -> EmailNaoEnviado:
    """Registra o motivo técnico (sem senha) no log e devolve o erro genérico para o usuário."""
    log.error("SMTP: %s", motivo)
    return EmailNaoEnviado("Não foi possível enviar o e-mail agora. Tente novamente em instantes.")


def _configuracao() -> dict:
    host = _env("SMTP_HOST")
    try:
        porta = int(_env("SMTP_PORT", "587"))
    except ValueError:
        raise _falha("SMTP_PORT inválida (use um número, ex.: 587)") from None
    modo = _env("SMTP_TLS", "ssl" if porta == 465 else "1").lower()
    if modo not in ("1", "ssl", "0"):
        raise _falha("SMTP_TLS inválido (use 1 = STARTTLS, ssl ou 0)")
    usuario = _env("SMTP_USER")
    remetente = _env("SMTP_FROM") or usuario
    if "@" not in remetente:
        raise _falha("SMTP_FROM ausente ou inválido: informe um e-mail remetente verificado no provedor (ex.: no-reply@seudominio)")
    if usuario and remetente == usuario and host.endswith("brevo.com"):
        raise _falha("no Brevo, SMTP_FROM precisa ser um remetente verificado; o login SMTP (…@smtp-brevo.com) não serve como remetente")
    return {"host": host, "porta": porta, "modo": modo, "usuario": usuario, "senha": _env("SMTP_PASSWORD"), "remetente": remetente}


def enviar_codigo(destino: str, codigo: str, finalidade: str, validade_min: int) -> None:
    if not smtp_configurado():
        if os.getenv("CODIGO_NO_LOG") == "1":
            log.warning("[DEV] CODIGO_NO_LOG=1, e-mail NÃO enviado. Código (%s) para %s: %s", finalidade, destino, codigo)
            return
        log.error("SMTP_HOST não configurado: não foi possível enviar o código para %s", destino)
        raise EmailNaoEnviado("O envio de e-mail não está configurado no servidor. Fale com o administrador.")

    cfg = _configuracao()
    msg = EmailMessage()
    msg["Subject"] = ASSUNTO[finalidade]
    msg["From"] = cfg["remetente"]
    msg["To"] = destino
    msg.set_content(
        f"Seu código para {MOTIVO[finalidade]}:\n\n    {codigo}\n\n"
        f"Ele vale por {validade_min} minutos e só pode ser usado uma vez.\n"
        "Se não foi você quem pediu, ignore este e-mail. Ninguém do AgendaSH pede esse código."
    )
    onde = f"{cfg['host']}:{cfg['porta']}"
    try:
        if cfg["modo"] == "ssl":
            s = smtplib.SMTP_SSL(cfg["host"], cfg["porta"], timeout=20, context=ssl.create_default_context())
        else:
            s = smtplib.SMTP(cfg["host"], cfg["porta"], timeout=20)
        with s:
            if cfg["modo"] == "1":
                s.starttls(context=ssl.create_default_context())
            if cfg["usuario"]:
                s.login(cfg["usuario"], cfg["senha"])
            s.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        raise _falha(f"{onde} recusou o login: confira SMTP_USER e SMTP_PASSWORD (no Brevo use a chave SMTP, não a senha da conta)") from None
    except smtplib.SMTPSenderRefused:
        raise _falha(f"{onde} recusou o remetente {cfg['remetente']}: verifique esse e-mail no provedor") from None
    except smtplib.SMTPRecipientsRefused:
        raise _falha(f"{onde} recusou o destinatário {destino}") from None
    except ssl.SSLError as e:
        raise _falha(f"falha TLS com {onde} ({e.reason or e}): confira SMTP_PORT e SMTP_TLS (587 = 1, 465 = ssl)") from None
    except (OSError, smtplib.SMTPException) as e:
        raise _falha(f"não foi possível falar com {onde}: {type(e).__name__}: {e}") from None
