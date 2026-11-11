import asyncio
import sys
sys.path.append(".")
from datetime import datetime
from app.services.email_service import email_service

async def main():
    await email_service.send_agendamento_email(
        cliente_email="teste@aluno.com",
        cliente_nome="João Teste",
        agendamento_id=123,
        data_hora=datetime.now()
    )

asyncio.run(main())