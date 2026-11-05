COLS = "id_usuario, nome, email, criado_em"


def listar(conn):
    return conn.execute(f"SELECT {COLS} FROM usuario ORDER BY nome").fetchall()


def buscar(conn, id_usuario: int):
    return conn.execute(f"SELECT {COLS} FROM usuario WHERE id_usuario = %s", (id_usuario,)).fetchone()


def buscar_por_email(conn, email: str):
    """Retorna também senha_hash (uso interno do login)."""
    return conn.execute("SELECT * FROM usuario WHERE email = %s", (email,)).fetchone()


def criar(conn, nome: str, email: str, senha_hash: str):
    return conn.execute(
        f"INSERT INTO usuario (nome, email, senha_hash) VALUES (%s, %s, %s) RETURNING {COLS}",
        (nome, email, senha_hash),
    ).fetchone()


def atualizar(conn, id_usuario: int, nome: str | None, email: str | None):
    return conn.execute(
        f"""UPDATE usuario SET nome = COALESCE(%s, nome), email = COALESCE(%s, email)
            WHERE id_usuario = %s RETURNING {COLS}""",
        (nome, email, id_usuario),
    ).fetchone()


def remover(conn, id_usuario: int) -> bool:
    return conn.execute("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,)).rowcount > 0
