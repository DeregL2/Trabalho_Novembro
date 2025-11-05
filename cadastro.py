import re
import bcrypt
from database import session, Usuario

def cadastrar():
    """
    Função para cadastrar novos usuários no banco de dados.
    Faz validação completa de e-mail e senha, gera o hash da senha
    e salva o usuário no banco de dados.
    """
    while True:
        print("\n--- CADASTRO DE USUÁRIO ---")
        nome = input("Digite seu nome: ")
        email = input("Digite seu e-mail: ")
        senha = input("Digite sua senha: ")
        confirmacao_senha = input("Confirme sua senha: ")

        # --- Validação de e-mail ---
        padrao_email = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.fullmatch(padrao_email, email):
            print("❌ E-mail inválido! Exemplo: usuario@dominio.com")
            continue

        # --- Validação de senha ---
        padrao_senha = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%&*!?]).{8,}$'
        if not re.fullmatch(padrao_senha, senha):
            print("❌ Senha inválida!")
            print("A senha deve conter:")
            print("- Pelo menos 8 caracteres")
            print("- Uma letra maiúscula")
            print("- Uma letra minúscula")
            print("- Um número")
            print("- Um caractere especial (@#$%&*!?)")
            continue

        # --- Confirmação de senha ---
        if senha != confirmacao_senha:
            print("❌ As senhas não conferem. Tente novamente.")
            continue

        # --- Aceite da política ---
        aceita = input("Você aceita a política de privacidade? (s/n): ").lower()
        if aceita != 's':
            print("⚠️ É necessário aceitar a política de privacidade para prosseguir.")
            continue

        # --- Criação do hash da senha ---
        # O bcrypt gera um hash seguro e aleatório (com salt automático)
        hash_senha = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())

        # --- Criação do objeto de usuário ---
        novo_usuario = Usuario(
            nome=nome.strip(),
            email=email.lower().strip(),
            hash_senha=hash_senha.decode("utf-8")  # Salva o hash como texto no banco
        )

        # --- Inserção no banco de dados ---
        try:
            session.add(novo_usuario)
            session.commit()
            print(f"✅ Cadastro concluído com sucesso! Bem-vindo, {nome}.")
            break
        except Exception as e:
            session.rollback()
            # Tratamento amigável para erro de duplicação de e-mail
            if "Duplicate" in str(e) or "UNIQUE" in str(e):
                print("⚠️ E-mail já cadastrado. Tente outro ou faça login.")
            else:
                print("❌ Erro ao cadastrar usuário:", e)
