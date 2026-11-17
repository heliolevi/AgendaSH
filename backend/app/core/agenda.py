"""Conflito de horário entre reuniões E eventos: uma sala não pode ter os dois ao mesmo tempo."""


def sala_ocupada(conn, id_sala: int, inicio, fim, ignorar_tipo: str | None = None, ignorar_id: int | None = None) -> bool:
    """True se a sala já tem reunião ou evento sobrepondo [inicio, fim).
    `ignorar_tipo` ('reuniao' | 'evento') + `ignorar_id` excluem o próprio registro numa edição."""
    return conn.execute(
        """SELECT 1 FROM (
               SELECT 'reuniao' AS tipo, id_reuniao AS id, id_sala, data_inicio, data_fim FROM reuniao
               UNION ALL
               SELECT 'evento', id_eventos, id_sala, data_inicio, data_fim FROM eventos
           ) x
           WHERE id_sala = %(sala)s AND data_inicio < %(fim)s AND data_fim > %(inicio)s
             AND (%(ign)s::int IS NULL OR NOT (tipo = %(tipo)s::text AND id = %(ign)s::int))
           LIMIT 1""",
        {"sala": id_sala, "inicio": inicio, "fim": fim, "tipo": ignorar_tipo, "ign": ignorar_id},
    ).fetchone() is not None
