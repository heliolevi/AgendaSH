"""SQL da tabela verificacao_email. Datas comparadas no banco (now()) para não depender do fuso do servidor."""


def segundos_desde_ultimo(conn, email: str, finalidade: str) -> float | None:
    r = conn.execute(
        "SELECT EXTRACT(EPOCH FROM (now() - max(criado_em))) AS s FROM verificacao_email WHERE email = %s AND finalidade = %s",
        (email, finalidade),
    ).fetchone()
    return None if r["s"] is None else float(r["s"])


def contar_ultima_hora(conn, email: str, finalidade: str) -> int:
    return conn.execute(
        """SELECT count(*) AS n FROM verificacao_email
           WHERE email = %s AND finalidade = %s AND criado_em > now() - interval '1 hour'""",
        (email, finalidade),
    ).fetchone()["n"]


def invalidar_anteriores(conn, email: str, finalidade: str) -> None:
    conn.execute(
        "UPDATE verificacao_email SET usado = TRUE WHERE email = %s AND finalidade = %s AND NOT usado",
        (email, finalidade),
    )


def criar(conn, email: str, finalidade: str, codigo_hash: str, validade_min: int) -> None:
    conn.execute(
        """INSERT INTO verificacao_email (email, finalidade, codigo_hash, expira_em)
           VALUES (%s, %s, %s, now() + make_interval(mins => %s))""",
        (email, finalidade, codigo_hash, validade_min),
    )


def buscar_ativo(conn, email: str, finalidade: str):
    return conn.execute(
        """SELECT id_verificacao, codigo_hash, tentativas FROM verificacao_email
           WHERE email = %s AND finalidade = %s AND NOT usado AND expira_em > now()
           ORDER BY criado_em DESC LIMIT 1""",
        (email, finalidade),
    ).fetchone()


def somar_tentativa(conn, id_verificacao: int) -> None:
    conn.execute("UPDATE verificacao_email SET tentativas = tentativas + 1 WHERE id_verificacao = %s", (id_verificacao,))


def marcar_usado(conn, id_verificacao: int) -> None:
    conn.execute("UPDATE verificacao_email SET usado = TRUE WHERE id_verificacao = %s", (id_verificacao,))
