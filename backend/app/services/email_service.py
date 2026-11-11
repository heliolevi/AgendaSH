import os
from datetime import datetime

# Lê do .env
EMAIL_TEST_MODE = os.getenv("EMAIL_TEST_MODE", "true").lower() == "true"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

class EmailService:
    def __init__(self):
        self.test_mode = EMAIL_TEST_MODE

    async def send_agendamento_email(self, cliente_email: str, cliente_nome: str, agendamento_id: int, data_hora: datetime):
        link_view = f"{FRONTEND_URL}/agendamentos/{agendamento_id}"
        link_cancel = f"{FRONTEND_URL}/agendamentos/{agendamento_id}/cancelar"

        if self.test_mode:
            print("\n" + "="*60)
            print(f"📅 [MODO TESTE - AGENDAMENTO]")
            print(f"Para: {cliente_email} ({cliente_nome})")
            print(f"ID: {agendamento_id}")
            print(f"Data: {data_hora}")
            print(f"Link View: {link_view}")
            print(f"Link Cancelar: {link_cancel}")
            print("="*60 + "\n")
            return {"test_mode": True, "link": link_view}

        
        print(f"Enviando e-mail real para {cliente_email}")
        return {"test_mode": False}

email_service = EmailService()