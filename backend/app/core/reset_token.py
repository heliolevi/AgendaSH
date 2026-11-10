"""Token assinado (HMAC-SHA256) para redefinir senha. Só biblioteca padrão.

Formato: base64url(json{u: id_usuario, f: impressão do hash atual, e: expira em}) + "." + assinatura.
A impressão (`f`) amarra o token ao hash de senha vigente: depois de trocar a senha o link morre (uso único).
Segredo: variável RESET_SECRET. Sem ela, usa um segredo aleatório do processo (links não sobrevivem a reinício).
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time

log = logging.getLogger("agendash")

TTL_SEGUNDOS = int(os.getenv("RESET_TTL_MINUTOS", "30")) * 60
_SEGREDO = (os.getenv("RESET_SECRET") or "").encode()
if not _SEGREDO:
    _SEGREDO = secrets.token_bytes(32)
    log.warning("RESET_SECRET não definido: usando segredo temporário (links de recuperação caem ao reiniciar).")


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _assinar(corpo: str) -> str:
    return _b64(hmac.new(_SEGREDO, corpo.encode(), hashlib.sha256).digest())


def impressao(senha_hash: str) -> str:
    return hashlib.sha256(senha_hash.encode()).hexdigest()[:16]


def gerar(id_usuario: int, senha_hash: str, agora: float | None = None) -> str:
    dados = {"u": id_usuario, "f": impressao(senha_hash), "e": int((agora or time.time()) + TTL_SEGUNDOS)}
    corpo = _b64(json.dumps(dados, separators=(",", ":")).encode())
    return f"{corpo}.{_assinar(corpo)}"


def ler(token: str, agora: float | None = None) -> dict | None:
    """Devolve {u, f, e} se a assinatura e a validade estiverem corretas; senão None."""
    try:
        corpo, assinatura = token.split(".", 1)
        if not hmac.compare_digest(assinatura, _assinar(corpo)):
            return None
        dados = json.loads(_unb64(corpo))
        if dados["e"] < (agora or time.time()):
            return None
        return {"u": int(dados["u"]), "f": str(dados["f"]), "e": int(dados["e"])}
    except (ValueError, KeyError, TypeError):
        return None
