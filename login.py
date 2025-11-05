from flask import Flask, render_template, request, redirect, url_for, session, flash
# --- CORREÇÃO DE IMPORT ---
# Importamos Usuario e session direto do 'database.py', que é onde eles são criados.
from database import Usuario, session as db_session
from dotenv import load_dotenv
from email.message import EmailMessage
# Import 'datetime' e 'timedelta'
from datetime import datetime, timedelta, UTC 
import bcrypt
import os
import smtplib
import random
# Imports que faltavam para a rota de cadastro
import re 

codigos_2fa = {}  # armazena temporariamente os códigos enviados
falhas_login = {} # NOVO: armazena as tentativas de login
LIMITE_FALHAS = 5 # NOVO: define o limite de tentativas

# ==========================
# 🔧 CONFIGURAÇÃO DO FLASK
# ==========================
app = Flask(__name__)
app.secret_key = "segredo_super_seguro"  # 🔒 usada para proteger sessões

# ==========================
# 📬 CONFIGURAÇÃO DO E-MAIL (2FA)
# ==========================
load_dotenv()
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# ==========================
# 🔐 CONFIGURAÇÃO DO 2FA
# ==========================
CODIGO_EXPIRA_MINUTOS = 5  # tempo de validade do código
# A linha duplicada de 'codigos_2fa' foi removida daqui.

# ==========================
# 🚀 NOVAS ROTAS (CADASTRO)
# ==========================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """
    Página de cadastro de novos usuários.
    - GET: Mostra o formulário de cadastro.
    - POST: Valida e processa os dados do formulário.
    """
    
    # Se o método for POST, o usuário enviou o formulário
    if request.method == "POST":
        # 1. Coleta os dados do formulário
        nome = request.form["nome"].strip()
        email = request.form["email"].lower().strip()
        senha = request.form["senha"]
        confirmacao_senha = request.form["confirmacao"]
        
        # 2. Validação (lógica adaptada do seu cadastros.py)
        
        # 2.1. Validação de e-mail
        padrao_email = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.fullmatch(padrao_email, email):
            flash("E-mail inválido! (Ex: usuario@dominio.com)", "erro")
            return redirect(url_for("cadastro"))

        # 2.2. Validação de força da senha
        padrao_senha = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%&*!?]).{8,}$'
        if not re.fullmatch(padrao_senha, senha):
            flash("Senha inválida! (Deve ter 8+ caracteres, maiúscula, minúscula, número e especial @#$%&*!?)", "erro_senha")
            return redirect(url_for("cadastro"))

        # 2.3. Confirmação de senha
        if senha != confirmacao_senha:
            flash("As senhas não conferem.", "erro")
            return redirect(url_for("cadastro"))

        # 2.4. Verifica se os termos foram aceitos
        aceite = request.form.get("termos")
        if not aceite:
            flash("Você deve aceitar os Termos de Uso e Política de Privacidade para continuar.", "erro")
            return redirect(url_for("cadastro"))

        # 2.5. Verifica se o e-mail já existe (era 2.4)
        usuario_existente = db_session.query(Usuario).filter_by(email=email).first()
        if usuario_existente:
            flash("Este e-mail já está cadastrado. Tente fazer login.", "erro")
            return redirect(url_for("cadastro"))

        # 3. Criação do Hash da Senha
        hash_senha = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # 4. Criação do novo usuário
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            hash_senha=hash_senha
            # twofa_ativo será 0 por padrão, conforme seu database.py
        )

        # 5. Salva no banco
        try:
            db_session.add(novo_usuario)
            db_session.commit()
            flash(f"✅ Cadastro concluído com sucesso! Bem-vindo, {nome}. Faça seu login.", "sucesso")
            return redirect(url_for("login"))
        except Exception as e:
            db_session.rollback()
            print(f"Erro ao salvar no banco: {e}")
            flash("❌ Erro inesperado ao criar cadastro. Tente novamente.", "erro")
            return redirect(url_for("cadastro"))

    # Se o método for GET, apenas mostre a página de cadastro
    return render_template("cadastro.html")


# ---------------- EMAIL -----------------
def enviar_email(destinatario, assunto, corpo):
    # (Seu código original, está ótimo)
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.set_content(corpo)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        print(f"📨 E-mail enviado com sucesso para {destinatario}")
        return True
    except Exception as e:
        print("⚠️ Erro ao enviar e-mail:", e)
        return False


# ---------------- LOGIN -----------------
@app.route("/", methods=["GET", "POST"])
def login():
    """
    Página de login.
    - Verifica e-mail e senha no banco.
    - Se o 2FA estiver ativo, envia o código por e-mail e redireciona para /mfa.
    """
    if request.method == "POST":
        email = request.form["email"].lower()
        senha = request.form["senha"]

        # --- NOVO BLOCO: VERIFICAÇÃO DE BLOQUEIO ---
        # .get(email, 0) significa "tente pegar o valor de falhas[email], se não existir, use 0"
        if falhas_login.get(email, 0) >= LIMITE_FALHAS:
            flash("Esta conta está temporariamente bloqueada por excesso de tentativas.", "erro")
            return render_template("login.html")
        # --- FIM DO BLOCO ---

        usuario = db_session.query(Usuario).filter_by(email=email).first()
        
        # (Corrigido) Use .encode() nas duas partes do bcrypt.checkpw
        if not usuario or not bcrypt.checkpw(senha.encode('utf-8'), usuario.hash_senha.encode('utf-8')):
            
            # --- NOVO BLOCO: INCREMENTO DE FALHA ---
            # Se o login falhou, adiciona +1 ao contador desse e-mail
            falhas_login[email] = falhas_login.get(email, 0) + 1
            tentativas_restantes = LIMITE_FALHAS - falhas_login[email]
            
            if tentativas_restantes > 0:
                flash(f"E-mail ou senha incorretos. {tentativas_restantes} tentativas restantes.", "erro")
            else:
                flash("E-mail ou senha incorretos. A conta foi bloqueada.", "erro")
            # --- FIM DO BLOCO ---
            
            return render_template("login.html")

        # --- NOVO BLOCO: LIMPA FALHAS NO SUCESSO ---
        # Se o login foi bem-sucedido, zeramos o contador de falhas para aquele e-mail
        if email in falhas_login:
            del falhas_login[email]
        # --- FIM DO BLOCO ---

        # Se 2FA ativo → gera e envia código
        if usuario.twofa_ativo:
            codigo = f"{random.randint(100000, 999999):06d}"
            # --- CORRIGIDO ABAIXO (para remover o DeprecationWarning) ---
            expira = datetime.now(UTC) + timedelta(minutes=CODIGO_EXPIRA_MINUTOS)
            codigos_2fa[email] = {"codigo": codigo, "expira": expira}

            corpo = (
                f"Olá, {usuario.nome}!\n\n"
                f"Seu código de autenticação é: {codigo}\n"
                f"Este código expira em {CODIGO_EXPIRA_MINUTOS} minutos."
            )

            enviar_email(email, "Código de autenticação 2FA", corpo)
            session["email_temp"] = email
            return redirect(url_for("mfa"))

        # Se 2FA desativado → login direto
        session["usuario_id"] = usuario.id
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ---------------- AUTENTICAÇÃO 2FA -----------------
@app.route("/mfa", methods=["GET", "POST"])
def mfa():
    """
    Página de validação do código 2FA.
    - Verifica se o código digitado é válido e ainda não expirou.
    """
    email_temp = session.get("email_temp")
    if not email_temp:
        return redirect(url_for("login"))

    if request.method == "POST":
        codigo_inserido = request.form["codigo"]
        entrada = codigos_2fa.get(email_temp)

        if not entrada:
            flash("Código expirado. Faça login novamente.", "erro")
            return redirect(url_for("login"))

        # --- CORRIGIDO ABAIXO (como você já tinha feito) ---
        if datetime.now(UTC) > entrada["expira"]:
            del codigos_2fa[email_temp]
            flash("Código expirado.", "erro")
            return redirect(url_for("login"))

        if codigo_inserido == entrada["codigo"]:
            usuario = db_session.query(Usuario).filter_by(email=email_temp).first()
            session["usuario_id"] = usuario.id
            del session["email_temp"]
            del codigos_2fa[email_temp]
            return redirect(url_for("dashboard"))

        flash("Código incorreto.", "erro")
    
    # --- CORRIGIDO ABAIXO (como você já tinha feito) ---
    return render_template("2mfa.html")


# ---------------- DASHBOARD -----------------
@app.route("/dashboard")
def dashboard():
    """
    Página principal após login.
    Mostra informações do usuário logado e opção de ativar/desativar o 2FA.
    """
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = db_session.query(Usuario).filter_by(id=session["usuario_id"]).first()
    return render_template("dashboard.html", usuario=usuario)


# ---------------- ATIVAR/DESATIVAR 2FA -----------------
@app.route("/ativar_2fa", methods=["POST"])
def ativar_2fa():
    """
    Ativa ou desativa o 2FA para o usuário logado.
    """
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario = db_session.query(Usuario).filter_by(id=session["usuario_id"]).first()
    
    # Lógica de toggle: Se 1, vira 0. Se 0, vira 1.
    usuario.twofa_ativo = 1 - usuario.twofa_ativo 
    
    db_session.commit()

    flash("✅ Autenticação em duas etapas atualizada com sucesso!", "sucesso")
    return redirect(url_for("dashboard"))


# ---------------- LOGOUT -----------------
@app.route("/logout")
def logout():
    """
    Encerra a sessão do usuário.
    """
    session.clear()
    flash("Logout realizado com sucesso.", "sucesso")
    return redirect(url_for("login"))


# ---------------- EXECUÇÃO -----------------
if __name__ == "__main__":
    app.run(debug=True)