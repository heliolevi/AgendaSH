import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

EMAIL_TEST_MODE = os.getenv("EMAIL_TEST_MODE", "true").lower() == "true"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Config SMTP (Gmail, Outlook, etc)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

class EmailService:
    def __init__(self):
        self.test_mode = EMAIL_TEST_MODE

    async def send_agendamento_email(self, cliente_email: str, cliente_nome: str, agendamento_id: int, data_hora: datetime):
        link_view = f"{FRONTEND_URL}/agendamentos/{agendamento_id}"
        link_cancel = f"{FRONTEND_URL}/agendamentos/{agendamento_id}/cancelar"

        subject = f"✅ Agendamento confirmado - {cliente_nome}"
        html = f"""
        <h2>Olá {cliente_nome},</h2>
        <p>Seu agendamento <b>#{agendamento_id}</b> foi confirmado para <b>{data_hora}</b>.</p>
        <p><a href="{link_view}" style="background:#2563eb;color:white;padding:10px 20px;text-decoration:none;border-radius:8px;">Ver agendamento</a></p>
        <p>Se precisar cancelar: <a href="{link_cancel}">{link_cancel}</a></p>
        """

        if self.test_mode:
            print("\n" + "="*60)
            print(f"📅 [MODO TESTE] Para: {cliente_email}")
            print(f"Link: {link_view}")
            print("="*60 + "\n")
            return {"test_mode": True, "link": link_view}

        # E-MAIL REAL
        if not SMTP_USER or not SMTP_PASS:
            print("[ERRO] SMTP_USER/SMTP_PASS não configurados no .env")
            return {"error": "SMTP não configurado"}

        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM
            msg['To'] = cliente_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            
            print(f"✅ E-mail real enviado para {cliente_email}")
            return {"sent": True}
        except Exception as e:
            print(f"❌ Falha ao enviar e-mail: {e}")
            return {"error": str(e)}

email_service = EmailService()