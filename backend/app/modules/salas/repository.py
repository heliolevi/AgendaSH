def listar(conn):
    return conn.execute("SELECT * FROM sala ORDER BY nome").fetchall()


def buscar(conn, id_sala: int):
    return conn.execute("SELECT * FROM sala WHERE id_sala = %s", (id_sala,)).fetchone()


def criar(conn, d: dict):
    return conn.execute(
        """INSERT INTO sala (nome, capacidade, tipo, localizacao_link)
           VALUES (%(nome)s, %(capacidade)s, %(tipo)s, %(localizacao_link)s) RETURNING *""",
        d,
    ).fetchone()


def atualizar(conn, id_sala: int, d: dict):
    return conn.execute(
        """UPDATE sala SET nome = %(nome)s, capacidade = %(capacidade)s,
                  tipo = %(tipo)s, localizacao_link = %(localizacao_link)s
           WHERE id_sala = %(id_sala)s RETURNING *""",
        {**d, "id_sala": id_sala},
    ).fetchone()


def remover(conn, id_sala: int) -> bool:
    return conn.execute("DELETE FROM sala WHERE id_sala = %s", (id_sala,)).rowcount > 0
