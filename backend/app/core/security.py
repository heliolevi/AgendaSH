from passlib.hash import pbkdf2_sha256


def hash_senha(senha: str) -> str:
    return pbkdf2_sha256.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return pbkdf2_sha256.verify(senha, senha_hash)
