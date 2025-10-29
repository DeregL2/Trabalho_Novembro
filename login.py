from cadastro import session, Usuario
from dotenv import load_dotenv
import os
import bcrypt
import smtplib
from email.message import EmailMessage
import random
from datetime import datetime, timedelta

# --- Carrega variáveis do .env ---
load_dotenv()
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# --- Configurações de 2FA ---
CODIGO_VALIDADE_MINUTOS = 5
cache_2fa = {}

def gerar_codigo_2fa():
    """Gera código numérico de 6 dígitos para 2FA"""
    return f"{random.randint(100000, 999999):06d}"

def enviar_email(destino, assunto, corpo):
    """Envia e-mail com código 2FA"""
    if not SMTP_USER or not SMTP_PASS:
        print("Configuração SMTP ausente.")
        return False

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = destino
    msg["Subject"] = assunto
    msg.set_content(corpo)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print("Erro ao enviar e-mail:", e)
        return False

def login():
    """Função de login com senha + 2FA por e-mail"""
    while True:
        print("\n--- LOGIN ---")
        validacao_email = input("Insira seu e-mail (ou 0 para voltar): ")
        if validacao_email == "0":
            return

        validacao_senha = input("Insira sua senha: ")

        usuario = session.query(Usuario).filter_by(email=validacao_email.lower()).first()
        if not usuario or not bcrypt.checkpw(validacao_senha.encode("utf-8"), usuario.hash_senha.encode("utf-8")):
            print("E-mail ou senha incorreta.")
            continue

        # --- Gera código 2FA ---
        codigo = gerar_codigo_2fa()
        expira_em = datetime.utcnow() + timedelta(minutes=CODIGO_VALIDADE_MINUTOS)
        cache_2fa[validacao_email.lower()] = {"codigo": codigo, "expira_em": expira_em}

        assunto = "Seu código de autenticação (2FA)"
        corpo = f"Olá {usuario.nome},\nSeu código de autenticação é: {codigo}\nExpira em {CODIGO_VALIDADE_MINUTOS} minutos."

        if not enviar_email(validacao_email, assunto, corpo):
            print("Não foi possível enviar o código. Tente novamente mais tarde.")
            return

        tentativa = input("Digite o código enviado por e-mail (ou 0 para cancelar): ")
        if tentativa == "0":
            print("Autenticação cancelada.")
            return

        entrada_cache = cache_2fa.get(validacao_email.lower())
        agora = datetime.utcnow()
        if not entrada_cache or agora > entrada_cache["expira_em"]:
            del cache_2fa[validacao_email.lower()]
            print("Código expirado. Faça login novamente.")
            continue

        if tentativa == entrada_cache["codigo"]:
            del cache_2fa[validacao_email.lower()]
            print(f"Login completo! Bem-vindo, {usuario.nome}")
            return
        else:
            print("Código 2FA incorreto.")
            continue
