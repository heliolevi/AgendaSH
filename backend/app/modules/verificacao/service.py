"""Regras dos códigos de 6 dígitos enviados por e-mail (cadastro e redefinição de senha).

- vale CODIGO_TTL_MINUTOS (padrão 10) e só uma vez; um código novo invalida o anterior;
- no máximo 1 envio por minuto e 5 por hora para cada e-mail/finalidade;
- 5 tentativas erradas invalidam o código;
- só o hash (HMAC) fica no banco, nunca o código.
"""
import hashlib
import hmac
import logging
import os
import secrets

from fastapi import HTTPException

from app.modules.verificacao import repository as repo

log = logging.getLogger("agendash")

VALIDADE_MIN = int(os.getenv("CODIGO_TTL_MINUTOS", "10"))
INTERVALO_SEG = int(os.getenv("CODIGO_INTERVALO_SEGUNDOS", "60"))
MAX_POR_HORA = int(os.getenv("CODIGO_MAX_POR_HORA", "5"))
MAX_TENTATIVAS = 5

_SEGREDO = (os.getenv("CODIGO_SECRET") or "").encode()
if not _SEGREDO:
    _SEGREDO = secrets.token_bytes(32)
    log.warning("CODIGO_SECRET não definido: códigos pendentes deixam de valer ao reiniciar o servidor.")


def _hash(email: str, finalidade: str, codigo: str) -> str:
    return hmac.new(_SEGREDO, f"{email}|{finalidade}|{codigo}".encode(), hashlib.sha256).hexdigest()


def emitir(conn, email: str, finalidade: str) -> str:
    """Grava um código novo (invalidando os anteriores) e devolve o texto para enviar por e-mail."""
    desde = repo.segundos_desde_ultimo(conn, email, finalidade)
    if desde is not None and desde < INTERVALO_SEG:
        espera = int(INTERVALO_SEG - desde) + 1
        raise HTTPException(429, f"Aguarde {espera}s para pedir um novo código.")
    if repo.contar_ultima_hora(conn, email, finalidade) >= MAX_POR_HORA:
        raise HTTPException(429, "Muitos pedidos de código. Tente novamente mais tarde.")
    codigo = f"{secrets.randbelow(10**6):06d}"
    repo.invalidar_anteriores(conn, email, finalidade)
    repo.criar(conn, email, finalidade, _hash(email, finalidade, codigo), VALIDADE_MIN)
    return codigo


def validar(conn, email: str, finalidade: str, codigo: str) -> None:
    """Confere e consome o código. Em caso de sucesso o uso só é confirmado junto com o resto da requisição."""
    invalido = HTTPException(400, "Código inválido ou expirado.")
    ativo = repo.buscar_ativo(conn, email, finalidade)
    if not ativo or ativo["tentativas"] >= MAX_TENTATIVAS:
        raise invalido
    if not hmac.compare_digest(ativo["codigo_hash"], _hash(email, finalidade, codigo)):
        repo.somar_tentativa(conn, ativo["id_verificacao"])
        conn.commit()  # o contador precisa sobreviver ao rollback que a exceção provoca
        raise invalido
    repo.marcar_usado(conn, ativo["id_verificacao"])
