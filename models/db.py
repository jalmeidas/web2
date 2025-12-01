from supabase import Client
from postgrest.exceptions import APIError
import bcrypt

supabase: Client = None


def set_supabase_client(client: Client):
    global supabase
    supabase = client


# CREATE



def inserir_fornecedor(nome_fornecedor):
    return supabase.table("FORNECEDOR").insert(
        {"nome_fornecedor": nome_fornecedor}
    ).execute()


def inserir_produto(nome_produto, custo_produto_Unit, valor_venda_Unit, 
                    id_local, id_categoria, id_fornecedor,
                    quantidade=0, estoque_minimo=0):
    return supabase.table("PRODUTOS").insert({
        "nome_produto": nome_produto,
        "custo_produto_Unit": custo_produto_Unit,
        "valor_venda_Unit": valor_venda_Unit,
        "id_local": id_local,
        "id_categoria": id_categoria,
        "id_fornecedor": id_fornecedor,
        "quantidade": quantidade,        # novo
        "estoque_minimo": estoque_minimo, # novo
    }).execute()



def inserir_usuario(nome_usuario, tipo_usuario, senha_usuario):
    senha_bytes = senha_usuario.encode("utf-8")
    salt = bcrypt.gensalt()
    hash_senha = bcrypt.hashpw(senha_bytes, salt).decode("utf-8")

    return supabase.table("USUARIOS").insert(
        {
            "nome_usuario": nome_usuario,
            "tipo_usuario": tipo_usuario,
            "senha_usuario": hash_senha,
        }
    ).execute()


def buscar_usuario_por_nome(nome_usuario):
    return (
        supabase.table("USUARIOS")
        .select("id, nome_usuario, tipo_usuario, senha_usuario")
        .eq("nome_usuario", nome_usuario)
        .single()
        .execute()
    )


def inserir_local_estoque(nome_local):
    return supabase.table("LOCAL_ESTOQUE").insert(
        {"nome_local": nome_local}
    ).execute()


# READ

def listar_usuarios():
    return supabase.table("USUARIOS").select("*").execute()


def listar_locais_estoque():
    return supabase.table("LOCAL_ESTOQUE").select("*").execute()


def listar_produtos():
    return supabase.table("PRODUTOS").select("*").execute()


def listar_fornecedores():
    return supabase.table("FORNECEDOR").select("*").execute()


# UPDATE (estoque)

def entrada_estoque(id_produto, quantidade):
    produto_resp = (
        supabase.table("PRODUTOS")
        .select("quantidade")
        .eq("id", id_produto)
        .single()
        .execute()
    )
    if not produto_resp.data:
        raise ValueError("Produto não encontrado")

    quantidade_atual = produto_resp.data["quantidade"]
    nova_quantidade = quantidade_atual + quantidade

    return (
        supabase.table("PRODUTOS")
        .update({"quantidade": nova_quantidade})
        .eq("id", id_produto)
        .execute()
    )


def saida_estoque(id_produto, quantidade):
    produto_resp = (
        supabase.table("PRODUTOS")
        .select("quantidade, estoque_minimo")
        .eq("id", id_produto)
        .single()
        .execute()
    )
    if not produto_resp.data:
        raise ValueError("Produto não encontrado")

    quantidade_atual = produto_resp.data["quantidade"]
    estoque_minimo = produto_resp.data.get("estoque_minimo", 0)

    if quantidade_atual < quantidade:
        raise ValueError("Estoque insuficiente")

    nova_quantidade = quantidade_atual - quantidade
    resp = (
        supabase.table("PRODUTOS")
        .update({"quantidade": nova_quantidade})
        .eq("id", id_produto)
        .execute()
    )

    if nova_quantidade < estoque_minimo:
        print("Atenção: Estoque abaixo do mínimo!")

    return resp


# DELETE

def deletar_usuario(id_usuario):
    return (
        supabase.table("USUARIOS")
        .delete()
        .eq("id", id_usuario)
        .execute()
    )





def deletar_fornecedor(id_fornecedor):
    try:
        return (
            supabase.table("FORNECEDOR")
            .delete()
            .eq("id", id_fornecedor)
            .execute()
        )
    except APIError:
        raise ValueError(
            "Não é possível deletar. Existem produtos usando este fornecedor. "
            "Delete os produtos primeiro."
        )


def deletar_produto(id_produto):
    return (
        supabase.table("PRODUTOS")
        .delete()
        .eq("id", id_produto)
        .execute()
    )


def deletar_local_estoque(id_local):
    try:
        return (
            supabase.table("LOCAL_ESTOQUE")
            .delete()
            .eq("id", id_local)
            .execute()
        )
    except APIError:
        raise ValueError(
            "Não é possível deletar. Existem produtos neste local. "
            "Delete os produtos primeiro."
        )


def listar_categorias():
    return supabase.table("CATEGORIA").select("*").execute()

def inserir_categoria(nome_categoria):
    return supabase.table("CATEGORIA").insert({"nome_categoria": nome_categoria}).execute()

def deletar_categoria(id_categoria):
    try:
        return supabase.table("CATEGORIA").delete().eq("id", id_categoria).execute()
    except APIError:
        raise ValueError("Não é possível deletar. Existem produtos usando esta categoria.")

