"""Middlewares globais.

Ordem (de fora para dentro): CORS -> RequestContext -> CatchAll -> rotas.
- CORS fica por fora para que até as respostas de erro levem os cabeçalhos CORS
  (sem isso o navegador mostra "NetworkError" em vez do erro real).
- RequestContext cria o request_id, mede o tempo, escreve o log e coloca cabeçalhos de segurança.
- CatchAll captura qualquer exceção não tratada e devolve JSON padronizado (sem traceback).
"""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.errors import erro_do_banco, resposta_erro

log = logging.getLogger("agendash")

CABECALHOS_SEGURANCA = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",  # respostas da API nunca ficam em cache
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex[:12]
        inicio = time.perf_counter()
        resposta = await call_next(request)
        ms = (time.perf_counter() - inicio) * 1000
        resposta.headers["X-Request-ID"] = request.state.request_id
        for k, v in CABECALHOS_SEGURANCA.items():
            resposta.headers.setdefault(k, v)
        # Só método, caminho e status: nunca corpo nem query string (podem ter senha/e-mail).
        log.info("%s %s -> %s (%.0f ms) [%s]", request.method, request.url.path, resposta.status_code, ms, request.state.request_id)
        return resposta


class CatchAllMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:  # noqa: BLE001 - é exatamente o papel deste middleware
            status, detail, codigo = erro_do_banco(exc)
            nivel = log.error if status >= 500 else log.warning
            nivel("%s %s falhou [%s]: %s: %s", request.method, request.url.path,
                  getattr(request.state, "request_id", "-"), type(exc).__name__, exc,
                  exc_info=status == 500)
            return resposta_erro(request, status, detail, codigo)
