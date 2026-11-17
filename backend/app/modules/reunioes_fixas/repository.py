COLS = "id_fixa, id_usuario, id_sala, titulo, descricao, dia_semana, hora_inicio, hora_fim, data_inicio, data_fim, criado_em"


def listar(conn, id_usuario: int | None = None, desde=None):
    """Séries ainda vigentes (sem data_fim ou com data_fim de `desde` em diante)."""
    return conn.execute(
        f"""SELECT {COLS} FROM reuniao_fixa
            WHERE (%(u)s::int IS NULL OR id_usuario = %(u)s)
              AND (%(desde)s::date IS NULL OR data_fim IS NULL OR data_fim >= %(desde)s)
            ORDER BY dia_semana, hora_inicio""",
        {"u": id_usuario, "desde": desde},
    ).fetchall()


def buscar(conn, id_fixa: int):
    return conn.execute(f"SELECT {COLS} FROM reuniao_fixa WHERE id_fixa = %s", (id_fixa,)).fetchone()


def criar(conn, d: dict):
    return conn.execute(
        f"""INSERT INTO reuniao_fixa (id_usuario, id_sala, titulo, descricao, dia_semana, hora_inicio, hora_fim,
                                      data_inicio, data_fim)
            VALUES (%(id_usuario)s, %(id_sala)s, %(titulo)s, %(descricao)s, %(dia_semana)s, %(hora_inicio)s,
                    %(hora_fim)s, %(data_inicio)s, %(data_fim)s)
            RETURNING {COLS}""",
        d,
    ).fetchone()


def ocorrencia_existe(conn, id_fixa: int, inicio) -> bool:
    return conn.execute(
        "SELECT 1 FROM reuniao WHERE id_fixa = %s AND data_inicio = %s LIMIT 1", (id_fixa, inicio)
    ).fetchone() is not None


def criar_ocorrencia(conn, fixa: dict, inicio, fim) -> None:
    conn.execute(
        """INSERT INTO reuniao (id_usuario, id_sala, titulo, descricao, data_inicio, data_fim, id_fixa)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (fixa["id_usuario"], fixa["id_sala"], fixa["titulo"], fixa["descricao"], inicio, fim, fixa["id_fixa"]),
    )


def remover(conn, id_fixa: int, a_partir_de) -> bool:
    """Apaga a série e as reuniões dela de `a_partir_de` em diante (com os convites)."""
    conn.execute(
        """DELETE FROM convite WHERE id_reuniao IN
           (SELECT id_reuniao FROM reuniao WHERE id_fixa = %s AND data_inicio >= %s)""",
        (id_fixa, a_partir_de),
    )
    conn.execute("DELETE FROM reuniao WHERE id_fixa = %s AND data_inicio >= %s", (id_fixa, a_partir_de))
    return conn.execute("DELETE FROM reuniao_fixa WHERE id_fixa = %s", (id_fixa,)).rowcount > 0
