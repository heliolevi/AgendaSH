import os

MODO_TESTE = os.getenv("EMAIL_MODO_TESTE", "true").lower() == "true"

def _pegar(reuniao, chave):
    # funciona se for dict ou objeto
    if isinstance(reuniao, dict):
        return reuniao.get(chave)
    return getattr(reuniao, chave, None)

def enviar_email_reuniao(reuniao):
    id_reuniao = _pegar(reuniao, "id")
    titulo = _pegar(reuniao, "titulo")
    email = _pegar(reuniao, "email")

    link = f"http://127.0.0.1:8000/reunioes/{id_reuniao}/confirmar"

    if MODO_TESTE:
        print("\n" + "="*50)
        print("EMAIL MODO TESTE - NAO ENVIADO DE VERDADE")
        print(f"Para: {email or 'sem email'}")
        print(f"Assunto: Confirmacao reuniao: {titulo}")
        print(f"Link: {link}")
        print("="*50 + "\n")
        return True

    return True