import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
    """)
    
    tabelas = cursor.fetchall()
    
    print("📋 Tabelas encontradas no seu Neon:")
    for tabela in tabelas:
        print(f" - {tabela[0]}")
        
    cursor.close()
    conn.close()

except Exception as error:
    print(f"❌ Erro ao ler o banco: {error}")
