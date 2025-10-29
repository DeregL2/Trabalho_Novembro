from cadastro import ARQUIVO_USUARIOS  # Importa a constante com o caminho do arquivo de usuários
from dotenv import load_dotenv         # Biblioteca para ler o arquivo .env
import os
import json
import bcrypt                          # Biblioteca para hash de senha
import smtplib                         # Biblioteca para envio de e-mail via SMTP
from email.message import EmailMessage
import random                          # Para gerar código 2FA aleatório
from datetime import datetime, timedelta

# --- Carrega variáveis do arquivo .env ---
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")  # Servidor SMTP (ex: smtp.gmail.com)
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  # Porta SMTP padrão (587 para TLS)
SMTP_USER = os.getenv("SMTP_USER")  # Usuário do e-mail (remetente)
SMTP_PASS = os.getenv("SMTP_PASS")  # Senha ou App Password

# --- Configuração do tempo de validade do código 2FA ---
CODIGO_VALIDADE_MINUTOS = 5

# Cache temporário em memória para códigos 2FA
# Estrutura: { "email@x.com": {"codigo": "123456", "expira_em": datetime_obj} }
cache_2fa = {}

# --- Função para gerar código 2FA ---
def gerar_codigo_2fa():
    """
    Gera um código numérico aleatório de 6 dígitos como string.
    """
    return f"{random.randint(100000, 999999):06d}"  # Formata com zeros à esquerda

# --- Função para enviar e-mail ---
def enviar_email(destino, assunto, corpo):
    """
    Envia um e-mail usando SMTP.
    Retorna True se enviado com sucesso, False caso contrário.
    """
    if not SMTP_USER or not SMTP_PASS:
        print("Configuração SMTP ausente. Configure SMTP_USER e SMTP_PASS no .env")
        return False

    # Cria o objeto da mensagem
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = destino
    msg["Subject"] = assunto
    msg.set_content(corpo)

    try:
        # Conexão SMTP com STARTTLS (TLS para segurança)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print("Erro ao enviar e-mail", e)
        return False

# --- Função de login com 2FA ---
def login():
    while True:
        print("\n--- LOGIN ---")
        # Solicita e-mail ou opção de voltar
        validacao_email = input("Insira seu e-mail (ou 0 para voltar): ")
        if validacao_email == "0":
            return  # Retorna ao menu principal

        # Solicita senha
        validacao_senha = input("Insira sua senha: ")

        # --- Carrega usuários do arquivo JSON ---
        try:
            with open(ARQUIVO_USUARIOS, "r") as f:
                dados = json.load(f)
        except FileNotFoundError:
            print("Email ou Senha incorretos!")
            return

        # Busca usuário pelo e-mail
        usuario_encontrado = None
        for usuario in dados:
            if usuario["email"].lower() == validacao_email.lower():
                usuario_encontrado = usuario
                break

        if not usuario_encontrado:
            print("Login ou Senha incorretos!")
            continue  # Volta ao início do loop

        # --- Verifica a senha ---
        hash_bytes = usuario_encontrado["hash_senha"].encode("utf-8")
        if not bcrypt.checkpw(validacao_senha.encode("utf-8"), hash_bytes):
            print("E-mail ou Senha incorreta")
            continue  # Senha incorreta, volta para tentar novamente

        # --- Gera o código 2FA ---
        codigo = gerar_codigo_2fa()
        expira_em = datetime.utcnow() + timedelta(minutes=CODIGO_VALIDADE_MINUTOS)
        cache_2fa[validacao_email.lower()] = {"codigo": codigo, "expira_em": expira_em}

        # --- Prepara e envia e-mail com o código 2FA ---
        assunto = "Seu código de autenticação (2FA)"
        corpo = (
            f"Olá {usuario_encontrado.get('nome','Usuário')},\n\n"
            f"Seu código de autenticação é: {codigo}\n"
            f"Esse código expira em {CODIGO_VALIDADE_MINUTOS} minutos.\n\n"
            "Se você não solicitou este código, ignore este e-mail.\n"
        )

        if not enviar_email(validacao_email, assunto, corpo):
            print("Não foi possível enviar o código por e-mail. Tente novamente mais tarde.")
            return

        # --- Solicita que o usuário digite o código 2FA ---
        tentativa = input("Digite o código enviado por e-mail (ou 0 para cancelar): ")
        if tentativa == "0":
            print("Autenticação cancelada pelo usuário.")
            return

        # --- Verifica validade do código ---
        entrada_cache = cache_2fa.get(validacao_email.lower())
        agora = datetime.utcnow()

        if not entrada_cache or agora > entrada_cache["expira_em"]:
            del cache_2fa[validacao_email.lower()]  # Remove código expirado
            print("Código expirado. Faça login novamente para gerar um novo código.")
            continue

        # --- Confirma o código 2FA ---
        if tentativa == entrada_cache["codigo"]:
            del cache_2fa[validacao_email.lower()]  # Remove código usado
            print(f"Login completo! Bem-vindo, {usuario_encontrado.get('nome','Usuário')}")
            return  # Login concluído
        else:
            print("Código 2FA incorreto.")
            continue
