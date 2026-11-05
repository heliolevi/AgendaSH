COLS = "id_reuniao, id_usuario, id_sala, titulo, descricao, data_inicio, data_fim"


def listar(conn, id_sala: int | None = None):
    return conn.execute(
        f"SELECT {COLS} FROM reuniao WHERE (%(s)s::int IS NULL OR id_sala = %(s)s) ORDER BY data_inicio",
        {"s": id_sala},
    ).fetchall()


def buscar(conn, id_reuniao: int):
    return conn.execute(f"SELECT {COLS} FROM reuniao WHERE id_reuniao = %s", (id_reuniao,)).fetchone()


def existe_conflito(conn, id_sala: int, inicio, fim, ignorar_id: int | None = None) -> bool:
    """True se a sala já tem reunião sobrepondo [inicio, fim)."""
    return conn.execute(
        """SELECT 1 FROM reuniao
           WHERE id_sala = %(sala)s AND data_inicio < %(fim)s AND data_fim > %(inicio)s
             AND (%(ign)s::int IS NULL OR id_reuniao <> %(ign)s) LIMIT 1""",
        {"sala": id_sala, "inicio": inicio, "fim": fim, "ign": ignorar_id},
    ).fetchone() is not None


def criar(conn, d: dict):
    return conn.execute(
        f"""INSERT INTO reuniao (id_usuario, id_sala, titulo, descricao, data_inicio, data_fim)
            VALUES (%(id_usuario)s, %(id_sala)s, %(titulo)s, %(descricao)s, %(data_inicio)s, %(data_fim)s)
            RETURNING {COLS}""",
        d,
    ).fetchone()


def atualizar(conn, id_reuniao: int, d: dict):
    return conn.execute(
        f"""UPDATE reuniao SET id_usuario = %(id_usuario)s, id_sala = %(id_sala)s, titulo = %(titulo)s,
                   descricao = %(descricao)s, data_inicio = %(data_inicio)s, data_fim = %(data_fim)s
            WHERE id_reuniao = %(id_reuniao)s RETURNING {COLS}""",
        {**d, "id_reuniao": id_reuniao},
    ).fetchone()


def remover(conn, id_reuniao: int) -> bool:
    # convites dependem da reunião (FK sem cascade): remover primeiro
    conn.execute("DELETE FROM convite WHERE id_reuniao = %s", (id_reuniao,))
    return conn.execute("DELETE FROM reuniao WHERE id_reuniao = %s", (id_reuniao,)).rowcount > 0
