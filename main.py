# main.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Usuario  # Certifique-se que o database.py está correto
from dotenv import load_dotenv
import os
import bcrypt

# --- Carrega variáveis de ambiente ---
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# --- Configura Flask ---
app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"  # Necessário para flash e session
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# --- Configura conexão com MySQL ---
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
db_session = DBSession()

# ----------------------
# Rotas do Flask
# ----------------------

# Página de login
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        usuario = db_session.query(Usuario).filter_by(email=email).first()
        if not usuario:
            flash("E-mail ou senha incorretos!")
            return redirect(url_for("index"))

        if bcrypt.checkpw(senha.encode("utf-8"), usuario.hash_senha.encode("utf-8")):
            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha incorretos!")
            return redirect(url_for("index"))

    return render_template("index.html")

# Página de cadastro
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]
        confirmacao = request.form["confirmacao"]
        termos = request.form.get("termos")

        # Valida senhas e termos
        if senha != confirmacao:
            flash("As senhas não coincidem!")
            return redirect(url_for("cadastro"))
        if not termos:
            flash("Você deve aceitar a política de privacidade!")
            return redirect(url_for("cadastro"))

        # Verifica se usuário já existe
        if db_session.query(Usuario).filter_by(email=email).first():
            flash("E-mail já cadastrado!")
            return redirect(url_for("cadastro"))

        # Cria hash da senha
        hash_senha = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Salva no banco
        novo_usuario = Usuario(nome=nome, email=email, hash_senha=hash_senha)
        db_session.add(novo_usuario)
        db_session.commit()

        flash("Cadastro realizado com sucesso! Faça login.")
        return redirect(url_for("index"))

    return render_template("cadastro.html")

# Dashboard (área restrita)
@app.route("/dashboard")
def dashboard():
    if "usuario_id" not in session:
        flash("Faça login para acessar o dashboard.")
        return redirect(url_for("index"))

    return render_template("dashboard.html", usuario_nome=session["usuario_nome"])

# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu com sucesso.")
    return redirect(url_for("index"))

# ----------------------
# Executa a aplicação
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
