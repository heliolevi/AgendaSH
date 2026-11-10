import logging

from passlib.hash import pbkdf2_sha256

log = logging.getLogger("agendash")


def hash_senha(senha: str) -> str:
    return pbkdf2_sha256.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return pbkdf2_sha256.verify(senha, senha_hash)
    except ValueError:
        # Hash gravado em outro formato (ex.: conta antiga em bcrypt). Não é erro 500: o login falha
        # e a pessoa pode usar "Recuperar senha" para gravar um hash válido.
        log.warning("Hash de senha em formato não suportado; login recusado.")
        return False
