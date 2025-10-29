# Importa bibliotecas
import re
import bcrypt
import json

# Arquivo para salvar usuários
ARQUIVO_USUARIOS = "usuarios.json"

# Função para salvar usuário em arquivo
def salvar_usuario(dados_usuario):
    try:
        with open(ARQUIVO_USUARIOS, "r") as f:
            usuarios = json.load(f)
    except FileNotFoundError:
        usuarios = []

    usuarios.append(dados_usuario)
    with open(ARQUIVO_USUARIOS, "w") as f:
        json.dump(usuarios, f, indent=4)

def cadastrar():
    # Cadastro de usuário
    while True:
        nome = input("Digite seu nome: ")
        email = input("Digite seu e-mail: ")
        senha = input("Digite sua senha: ")
        confirmacao_senha = input("Confirme sua senha: ")

        padrao_email = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        padrao_senha = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%&*!?]).{8,}$'

        # Validação de e-mail
        if not re.fullmatch(padrao_email, email):
            print("E-mail inválido!")
            continue  # volta para o início do loop

        # Validação de senha
        if not re.fullmatch(padrao_senha, senha):
            print("Senha inválida! Ela deve ter pelo menos 8 caracteres, uma maiúscula, uma minúscula, um número e um caractere especial (@#$%&*!?).")
            continue

        # Confirmação de senha
        if senha != confirmacao_senha:
            print("Senhas divergentes, tente novamente.")
            continue

        # Termos de Uso
        aceita = input("Você aceita os termos da política de privacidade? (s/n): ").lower()
        if aceita != 's':
            print("Você precisa aceitar a política de privacidade para se cadastrar.")
            continue

        # Gerar hash da senha (apenas depois de todas as validações)
        senha_bytes = senha.encode("utf-8")
        hash_senha = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())

        # Criar dicionário do usuário
        usuario = {
            "nome": nome,
            "email": email,
            "hash_senha": hash_senha.decode("utf-8")  # salva como string
        }

        # Salvar usuário no arquivo
        salvar_usuario(usuario)

        print("Cadastro concluído com sucesso! ✅")
        break

