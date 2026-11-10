"""Formato único de erro da API e handlers globais.

Toda resposta de erro tem o formato:
    {"detail": "mensagem legível", "codigo": "CODIGO_ESTAVEL", "request_id": "..."}
O front só precisa ler `detail`. Nunca devolvemos traceback, SQL nem dados do banco.
"""
import logging

import psycopg
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg import errors as pgerr
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("agendash")

CODIGOS_HTTP = {
    400: "REQUISICAO_INVALIDA", 401: "NAO_AUTENTICADO", 403: "SEM_PERMISSAO", 404: "NAO_ENCONTRADO",
    405: "METODO_NAO_PERMITIDO", 409: "CONFLITO", 422: "DADOS_INVALIDOS", 429: "MUITAS_TENTATIVAS",
}


def resposta_erro(request: Request, status: int, detail: str, codigo: str | None = None, **extra) -> JSONResponse:
    corpo = {
        "detail": detail,
        "codigo": codigo or CODIGOS_HTTP.get(status, "ERRO"),
        "request_id": getattr(request.state, "request_id", None),
        **extra,
    }
    return JSONResponse(corpo, status_code=status)


def erro_do_banco(exc: Exception) -> tuple[int, str, str]:
    """Converte exceção do psycopg em (status, mensagem, código). Mensagens genéricas de propósito."""
    if isinstance(exc, pgerr.UniqueViolation):
        return 409, "Registro já existe", "REGISTRO_DUPLICADO"
    if isinstance(exc, pgerr.ForeignKeyViolation):
        return 409, "Operação inválida: há registros relacionados", "REFERENCIA_INVALIDA"
    if isinstance(exc, (pgerr.NotNullViolation, pgerr.CheckViolation, pgerr.StringDataRightTruncation,
                        pgerr.InvalidTextRepresentation, pgerr.NumericValueOutOfRange, pgerr.InvalidDatetimeFormat)):
        return 400, "Dados inválidos", "DADOS_INVALIDOS"
    if isinstance(exc, pgerr.ExclusionViolation):
        return 409, "Horário indisponível", "CONFLITO_HORARIO"
    if isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError, TimeoutError)):
        return 503, "Serviço temporariamente indisponível. Tente novamente em instantes.", "BANCO_INDISPONIVEL"
    return 500, "Erro interno. Tente novamente mais tarde.", "ERRO_INTERNO"


_TRADUCOES = {
    "missing": "campo obrigatório",
    "string_too_short": "texto curto demais",
    "string_too_long": "texto longo demais",
    "int_parsing": "deve ser um número inteiro",
    "greater_than": "valor muito baixo",
    "datetime_from_date_parsing": "data/hora inválida",
    "datetime_parsing": "data/hora inválida",
    "json_invalid": "JSON inválido",
    "literal_error": "valor não permitido",
}


def _msg_validacao(e: dict) -> str:
    campo = ".".join(str(p) for p in e.get("loc", []) if p not in ("body", "query", "path"))
    if e.get("type") == "value_error":  # validadores nossos já vêm em português
        texto = str(e.get("msg", "")).removeprefix("Value error, ")
    else:
        texto = _TRADUCOES.get(e.get("type", ""), "valor inválido")
    return f"{campo}: {texto}" if campo else texto


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validacao(request: Request, exc: RequestValidationError):
        msgs = [_msg_validacao(e) for e in exc.errors()]
        return resposta_erro(request, 422, "; ".join(msgs), "DADOS_INVALIDOS", erros=msgs)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        resp = resposta_erro(request, exc.status_code, str(exc.detail))
        if exc.headers:
            resp.headers.update(exc.headers)
        return resp
