"""Limitador simples de tentativas em memoria (anti forca-bruta no login).

Guarda, por chave (ex.: "ip|email"), os horarios das ultimas falhas. Passou do limite
dentro da janela -> bloqueia por um tempo. E por processo (nao compartilha entre replicas);
para 1 instancia, como e o caso aqui, resolve o brute-force de senha. Em producao com varias
replicas, trocar por Redis.
"""
import threading
import time

_FALHAS: dict[str, list[float]] = {}
_LOCK = threading.Lock()

MAX_FALHAS = 5          # tentativas erradas...
JANELA_SEG = 15 * 60    # ...dentro de 15 min...
BLOQUEIO_SEG = 15 * 60  # ...bloqueiam a chave por 15 min.


def _limpar(agora: float, marcas: list[float]) -> list[float]:
    return [t for t in marcas if agora - t < JANELA_SEG]


def segundos_de_bloqueio(chave: str) -> int:
    """0 se liberado; senao, quantos segundos faltam para desbloquear."""
    agora = time.time()
    with _LOCK:
        marcas = _limpar(agora, _FALHAS.get(chave, []))
        _FALHAS[chave] = marcas
        if len(marcas) < MAX_FALHAS:
            return 0
        restante = int(marcas[-1] + BLOQUEIO_SEG - agora)
        return max(restante, 0)


def registrar_falha(chave: str) -> None:
    agora = time.time()
    with _LOCK:
        marcas = _limpar(agora, _FALHAS.get(chave, []))
        marcas.append(agora)
        _FALHAS[chave] = marcas


def limpar(chave: str) -> None:
    """Login deu certo: zera o contador daquela chave."""
    with _LOCK:
        _FALHAS.pop(chave, None)
