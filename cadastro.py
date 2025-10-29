import re
import bcrypt
from database import session, Usuario

def cadastrar():
    """
    Função para cadastrar novos usuários no banco de dados.
    Valida e-mail, senha e confirmação de senha.
    """
    while True:
        nome = input("Digite seu nome: ")
        email = input("Digite seu e-mail: ")
        senha = input("Digite sua senha: ")
        confirmacao_senha = input("Confirme sua senha: ")

        # --- Validações ---
        padrao_email = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        padrao_senha = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%&*!?]).{8,}$'

        if not re.fullmatch(padrao_email, email):
            print("E-mail inválido!")
            continue

        if not re.fullmatch(padrao_senha, senha):
            print("Senha inválida! Deve ter pelo menos 8 caracteres, uma maiúscula, uma minúscula, um número e um caractere especial.")
            continue

        if senha != confirmacao_senha:
            print("Senhas divergentes, tente novamente.")
            continue

        aceita = input("Você aceita a política de privacidade? (s/n): ").lower()
        if aceita != 's':
            print("É necessário aceitar a política de privacidade para se cadastrar.")
            continue

        # --- Hash da senha ---
        hash_senha = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())

        # --- Criação do usuário ---
        novo_usuario = Usuario(
            nome=nome,
            email=email.lower(),
            hash_senha=hash_senha.decode("utf-8")
        )

        try:
            session.add(novo_usuario)
            session.commit()
            print("Cadastro concluído com sucesso!")
            break
        except Exception as e:
            session.rollback()
            print("Erro ao cadastrar usuário. E-mail já cadastrado?" if "Duplicate" in str(e) else str(e))
