# Importa as funções de cadastro e login dos módulos correspondentes
from cadastro import cadastrar
from login import login

def menu():
    """
    Função principal que exibe o menu do sistema.
    Permite ao usuário escolher entre:
      - Cadastrar um novo usuário
      - Fazer login
      - Sair do programa
    """
    while True:
        # Exibe o menu principal
        print("\n=== MENU PRINCIPAL ===")
        print("1 - Cadastrar")   # Opção para criar novo usuário
        print("2 - Login")       # Opção para fazer login
        print("0 - Sair")        # Opção para encerrar o sistema

        # Solicita a escolha do usuário
        opcao = input("Escolha uma opção: ")

        # Avalia a escolha e chama a função correspondente
        if opcao == "1":
            cadastrar()  # Chama a função de cadastro
        elif opcao == "2":
            login()      # Chama a função de login
        elif opcao == "0":
            print("Saindo do sistema...")
            break        # Encerra o loop e finaliza o programa
        else:
            print("Opção inválida! Tente novamente.")  # Validação de entrada

# Ponto de entrada do programa
# Garante que o menu só será executado se o arquivo for rodado diretamente
if __name__ == "__main__":
    menu()
