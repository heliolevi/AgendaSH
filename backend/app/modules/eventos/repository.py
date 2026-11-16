COLS = "id_eventos, id_usuario, id_sala, titulo, descricao, data_inicio, data_fim"


def listar(conn, id_sala: int | None = None):
    return conn.execute(
        f"SELECT {COLS} FROM eventos WHERE (%(s)s::int IS NULL OR id_sala = %(s)s) ORDER BY data_inicio",
        {"s": id_sala},
    ).fetchall()


def buscar(conn, id_evento: int):
    return conn.execute(f"SELECT {COLS} FROM eventos WHERE id_eventos = %s", (id_evento,)).fetchone()


def criar(conn, d: dict):
    return conn.execute(
        f"""INSERT INTO eventos (id_usuario, id_sala, titulo, descricao, data_inicio, data_fim)
            VALUES (%(id_usuario)s, %(id_sala)s, %(titulo)s, %(descricao)s, %(data_inicio)s, %(data_fim)s)
            RETURNING {COLS}""",
        d,
    ).fetchone()


def atualizar(conn, id_evento: int, d: dict):
    return conn.execute(
        f"""UPDATE eventos SET id_usuario = %(id_usuario)s, id_sala = %(id_sala)s, titulo = %(titulo)s,
                   descricao = %(descricao)s, data_inicio = %(data_inicio)s, data_fim = %(data_fim)s
            WHERE id_eventos = %(id)s RETURNING {COLS}""",
        {**d, "id": id_evento},
    ).fetchone()


def remover(conn, id_evento: int) -> bool:
    return conn.execute("DELETE FROM eventos WHERE id_eventos = %s", (id_evento,)).rowcount > 0


def apagar_passados(conn, limite) -> int:
    """Apaga os eventos que terminaram antes de `limite`. Devolve quantos foram apagados."""
    return conn.execute("DELETE FROM eventos WHERE data_fim < %s", (limite,)).rowcount
