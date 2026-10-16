import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

SQL_COMMANDS = [
    """
    CREATE TABLE IF NOT EXISTS usuario(
        ID_usuario INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        senha_hash VARCHAR(200) NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    
    """
    CREATE TABLE IF NOT EXISTS sala(
        ID_sala INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        capacidade INT NOT NULL,
        tipo VARCHAR(250) NOT NULL,
        localizacao_link TEXT
    );
    """,
    
    """
    CREATE TABLE IF NOT EXISTS reuniao(
        ID_reuniao INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        ID_usuario INT,
        FOREIGN KEY (ID_usuario) REFERENCES usuario(ID_usuario),
        ID_sala INT,
        FOREIGN KEY (ID_sala) REFERENCES sala(ID_sala),
        titulo VARCHAR(200) NOT NULL,
        descricao TEXT,
        data_inicio TIMESTAMP NOT NULL,
        data_fim TIMESTAMP NOT NULL,
        comeca_em TIMESTAMP DEFAULT CURRENT_DATE
    );
    """,
    
    """
    CREATE TABLE IF NOT EXISTS convite(
        ID_reuniao INT,
        ID_usuario INT,
        status_resposta VARCHAR(100),
        data_hora TIMESTAMP,
        PRIMARY KEY (ID_reuniao, ID_usuario),
        FOREIGN KEY (ID_reuniao) REFERENCES reuniao(ID_reuniao),
        FOREIGN KEY (ID_usuario) REFERENCES usuario(ID_usuario)
    );
    """
]

try:
    print("🔄 Conectando ao banco de dados Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("🛠️ Criando as tabelas no banco de dados...")
    for command in SQL_COMMANDS:
        cursor.execute(command)

    conn.commit()
    print("🚀 Sucesso! Todas as 4 tabelas foram criadas com sucesso no seu Neon Console!")

    cursor.close()
    conn.close()

except Exception as error:
    print(f"❌ Ocorreu um erro ao criar as tabelas: {error}")
