"""Cria (ou promove) uma conta de ADMINISTRADOR, sem precisar do código por e-mail.
Uso local, para a equipe testar o painel admin. A senha é pedida no terminal (não aparece na tela)
e só o hash vai para o banco.

    cd backend
    .venv\\Scripts\\Activate.ps1
    python criar_admin.py

Se o e-mail já tiver conta, ela só vira admin (a senha continua a mesma).
"""
import getpass
import sys

import psycopg
from psycopg.rows import dict_row

from app.core.database import DATABASE_URL
from app.core.email_policy import validar_email_undb
from app.core.security import hash_senha

if not DATABASE_URL:
    sys.exit("DATABASE_URL não está no .env do backend.")

try:
    email = validar_email_undb(input("E-mail institucional (UNDB): "))[0]
except ValueError as e:
    sys.exit(str(e))

with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=30) as conn:
    conn.execute("ALTER TABLE usuario ADD COLUMN IF NOT EXISTS papel VARCHAR(20) NOT NULL DEFAULT 'membro'")
    existe = conn.execute("SELECT id_usuario, nome FROM usuario WHERE lower(email) = %s", (email,)).fetchone()
    if existe:
        conn.execute("UPDATE usuario SET papel = 'admin' WHERE id_usuario = %s", (existe["id_usuario"],))
        print(f"OK: {existe['nome']} ({email}) agora é admin. Entre com a senha que já usa.")
        sys.exit(0)

    nome = input("Nome completo: ").strip()
    if not nome:
        sys.exit("Informe o nome.")
    senha = getpass.getpass("Senha (mínimo 6 caracteres): ")
    if len(senha) < 6:
        sys.exit("A senha precisa de no mínimo 6 caracteres.")
    if senha != getpass.getpass("Repita a senha: "):
        sys.exit("As senhas não conferem.")

    colunas = {r["column_name"] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'usuario'").fetchall()}
    if "verificado" in colunas:
        conn.execute("INSERT INTO usuario (nome, email, senha_hash, papel, verificado) VALUES (%s, %s, %s, 'admin', TRUE)",
                     (nome, email, hash_senha(senha)))
    else:
        conn.execute("INSERT INTO usuario (nome, email, senha_hash, papel) VALUES (%s, %s, %s, 'admin')",
                     (nome, email, hash_senha(senha)))
    print(f"OK: conta de admin criada para {email}. Entre em login.html com esse e-mail e a senha que você digitou.")
