def listar(conn, id_reuniao: int | None = None, id_usuario: int | None = None):
    return conn.execute(
        """SELECT * FROM convite
           WHERE (%(r)s::int IS NULL OR id_reuniao = %(r)s)
             AND (%(u)s::int IS NULL OR id_usuario = %(u)s)""",
        {"r": id_reuniao, "u": id_usuario},
    ).fetchall()


def criar(conn, id_reuniao: int, id_usuario: int):
    return conn.execute(
        """INSERT INTO convite (id_reuniao, id_usuario, status_resposta)
           VALUES (%s, %s, 'pendente') RETURNING *""",
        (id_reuniao, id_usuario),
    ).fetchone()


def responder(conn, id_reuniao: int, id_usuario: int, status: str):
    return conn.execute(
        """UPDATE convite SET status_resposta = %s, data_hora = CURRENT_TIMESTAMP
           WHERE id_reuniao = %s AND id_usuario = %s RETURNING *""",
        (status, id_reuniao, id_usuario),
    ).fetchone()


def remover(conn, id_reuniao: int, id_usuario: int) -> bool:
    return conn.execute(
        "DELETE FROM convite WHERE id_reuniao = %s AND id_usuario = %s", (id_reuniao, id_usuario)
    ).rowcount > 0
