"""Autenticação por token (JWT HS256) — o "OAuth2 password flow" do FastAPI.

Por que HS256 feito à mão (hmac da stdlib) e não uma biblioteca:
- o projeto já assina códigos com hmac (módulo de verificação), então o padrão é o mesmo;
- não adiciona dependência nova para instalar no venv de todo mundo;
- é totalmente testável (tests/test_auth.py).

Fluxo:
- POST /auth/login (ou /auth/token) devolve um access_token;
- o front manda `Authorization: Bearer <token>` em toda chamada;
- `Depends(usuario_atual)` libera a rota para qualquer logado;
- `Depends(somente_admin)` libera só para papel == "admin".

Segurança:
- assinatura HMAC-SHA256 conferida com compare_digest (tempo constante);
- `exp` (expiração) obrigatório;
- sem JWT_SECRET o servidor usa um segredo aleatório por processo (tokens caem ao
  reiniciar) e registra um aviso — defina JWT_SECRET em produção.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

log = logging.getLogger("agendash")

ALGORITMO = "HS256"
EXPIRA_MIN = int(os.getenv("JWT_EXPIRA_MIN", "720"))  # 12 horas

_SEGREDO = (os.getenv("JWT_SECRET") or "").encode()
if not _SEGREDO:
    _SEGREDO = secrets.token_bytes(32)
    log.warning(
        "JWT_SECRET nao definido: tokens de sessao deixam de valer ao reiniciar o servidor. "
        "Defina um valor longo e aleatorio em producao."
    )

_HEADER = {"alg": ALGORITMO, "typ": "JWT"}

# auto_error=False: quando nao ha cabecalho, devolvemos nosso proprio 401 no formato da API.
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


def _b64url(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode("ascii")


def _b64url_dec(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _assinar(corpo: str) -> str:
    return _b64url(hmac.new(_SEGREDO, corpo.encode("ascii"), hashlib.sha256).digest())


def criar_token(id_usuario: int, papel: str, nome: str | None = None,
                email: str | None = None, expira_min: int | None = None) -> str:
    """Gera um access_token assinado para o usuario."""
    agora = int(time.time())
    payload = {
        "sub": str(id_usuario),
        "papel": papel,
        "nome": nome,
        "email": email,
        "iat": agora,
        "exp": agora + (expira_min or EXPIRA_MIN) * 60,
    }
    corpo = (
        _b64url(json.dumps(_HEADER, separators=(",", ":")).encode())
        + "."
        + _b64url(json.dumps(payload, separators=(",", ":")).encode())
    )
    return corpo + "." + _assinar(corpo)


def decodificar_token(token: str) -> dict:
    """Confere assinatura e expiracao. Levanta HTTPException(401) se o token nao presta."""
    invalido = HTTPException(401, "Sessao invalida. Entre novamente.")
    partes = token.split(".")
    if len(partes) != 3:
        raise invalido
    cabecalho, corpo, assinatura = partes
    if not hmac.compare_digest(_assinar(f"{cabecalho}.{corpo}"), assinatura):
        raise invalido
    try:
        payload = json.loads(_b64url_dec(corpo))
    except (ValueError, json.JSONDecodeError):
        raise invalido
    if not isinstance(payload, dict) or int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(401, "Sessao expirada. Entre novamente.")
    return payload


def usuario_atual(token: str | None = Depends(oauth2)) -> dict:
    """Dependencia: exige um Bearer token valido. Devolve os dados do usuario do token."""
    if not token:
        raise HTTPException(401, "Autenticacao necessaria.", headers={"WWW-Authenticate": "Bearer"})
    payload = decodificar_token(token)
    try:
        id_usuario = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(401, "Sessao invalida. Entre novamente.")
    return {
        "id_usuario": id_usuario,
        "papel": payload.get("papel", "membro"),
        "nome": payload.get("nome"),
        "email": payload.get("email"),
    }


def somente_admin(usuario: dict = Depends(usuario_atual)) -> dict:
    """Dependencia: alem de logado, o usuario precisa ter papel 'admin'."""
    if usuario.get("papel") != "admin":
        raise HTTPException(403, "Acesso restrito a administradores.")
    return usuario
