from supabase import create_client
import db

SUPABASE_URL = "https://xuaybixptiibbvgodjhi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1YXliaXhwdGlpYmJ2Z29kamhpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0NDE4NTcsImV4cCI6MjA4MDAxNzg1N30.4nbuZYOq9jPeOh_h9sthJ4odvQd83yTxe0YAIovCfd0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
db.set_supabase_client(supabase)

def mostrar_menu():
    print("\n=== CONTROLE DE ESTOQUE ===")
    print("1 - Cadastrar usuário")
    print("2 - Listar usuários")
    print("3 - Cadastrar categoria")
    print("4 - Cadastrar fornecedor")
    print("5 - Cadastrar produto")
    print("6 - Listar produtos")
    print("7 - Entrada em estoque")
    print("8 - Saída do estoque")
    print("0 - Sair")

def main():
    try:
        supabase.table("USUARIOS").select("id").limit(1).execute()
        print("✅ Conexão com Supabase OK!")
    except Exception as e:
        print("❌ Erro ao conectar no Supabase:", e)
        return

    while True:
        mostrar_menu()
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            nome = input("Nome do usuário: ")
            tipo = int(input("Tipo do usuário (1=admin, 2=operador,...): "))
            senha = input("Senha: ")
            resp = db.inserir_usuario(nome, tipo, senha)
            print("Usuário inserido:", resp.data)

        elif opcao == "2":
            resp = db.listar_usuarios()
            if resp.data:
                for u in resp.data:
                    print(u)
            else:
                print("Nenhum usuário encontrado.")

        elif opcao == "3":
            nome = input("Nome da categoria: ")
            resp = db.inserir_categoria(nome)
            print("Categoria inserida:", resp.data)

        elif opcao == "4":
            nome = input("Nome do fornecedor: ")
            resp = db.inserir_fornecedor(nome)
            print("Fornecedor inserido:", resp.data)

        elif opcao == "5":
            nome = input("Nome do produto: ")
            custo = float(input("Custo unitário: "))
            venda = float(input("Valor venda unitário: "))
            id_local = int(input("ID local estoque: "))
            id_categoria = int(input("ID categoria: "))
            id_fornecedor = int(input("ID fornecedor: "))
            resp = db.inserir_produto(
                nome, custo, venda, id_local, id_categoria, id_fornecedor
            )
            print("Produto inserido:", resp.data)

        elif opcao == "6":
            resp = db.listar_produtos()
            if resp.data:
                for p in resp.data:
                    print(p)
            else:
                print("Nenhum produto encontrado.")

        elif opcao == "7":
            id_prod = int(input("ID do produto: "))
            qtd = int(input("Quantidade entrada: "))
            resp = db.entrada_estoque(id_prod, qtd)
            print("Estoque atualizado:", resp.data)

        elif opcao == "8":
            id_prod = int(input("ID do produto: "))
            qtd = int(input("Quantidade saída: "))
            try:
                resp = db.saida_estoque(id_prod, qtd)
                print("Estoque atualizado:", resp.data)
            except ValueError as ve:
                print("Erro:", ve)

        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
