from supabase import Client

supabase: Client = None

def set_supabase_client(client: Client):
    global supabase
    supabase = client

def inserir_usuario(nome_usuario, tipo_usuario, senha_usuario):
    return supabase.table("USUARIOS").insert({
        "nome_usuario": nome_usuario,
        "tipo_usuario": tipo_usuario,
        "senha_usuario": senha_usuario,
    }).execute()

def listar_usuarios():
    return supabase.table("USUARIOS").select("*").execute()

def inserir_categoria(nome_categoria):
    return supabase.table("CATEGORIA").insert({"nome_categoria": nome_categoria}).execute()

def inserir_fornecedor(nome_fornecedor):
    return supabase.table("FORNECEDOR").insert({"nome_fornecedor": nome_fornecedor}).execute()

def inserir_produto(nome_produto, custo_produto_Unit, valor_venda_Unit, id_local, id_categoria, id_fornecedor):
    return supabase.table("PRODUTOS").insert({
        "nome_produto": nome_produto,
        "custo_produto_Unit": custo_produto_Unit,
        "valor_venda_Unit": valor_venda_Unit,
        "id_local": id_local,
        "id_categoria": id_categoria,
        "id_fornecedor": id_fornecedor,
    }).execute()

def listar_produtos():
    return supabase.table("PRODUTOS").select("*").execute()

def entrada_estoque(id_produto, quantidade):
    produto_resp = supabase.table("PRODUTOS").select("quantidade").eq("id", id_produto).single().execute()
    if not produto_resp.data:
        raise ValueError("Produto não encontrado")
    quantidade_atual = produto_resp.data["quantidade"]
    nova_quantidade = quantidade_atual + quantidade
    return supabase.table("PRODUTOS").update({"quantidade": nova_quantidade}).eq("id", id_produto).execute()

def saida_estoque(id_produto, quantidade):
    produto_resp = supabase.table("PRODUTOS").select("quantidade, estoque_minimo").eq("id", id_produto).single().execute()
    if not produto_resp.data:
        raise ValueError("Produto não encontrado")
    quantidade_atual = produto_resp.data["quantidade"]
    estoque_minimo = produto_resp.data.get("estoque_minimo", 0)
    if quantidade_atual < quantidade:
        raise ValueError("Estoque insuficiente")
    nova_quantidade = quantidade_atual - quantidade
    resp = supabase.table("PRODUTOS").update({"quantidade": nova_quantidade}).eq("id", id_produto).execute()
    if nova_quantidade < estoque_minimo:
        print("Atenção: Estoque abaixo do mínimo!")
    return resp

def inserir_local_estoque(nome_local):
    return supabase.table("LOCAL_ESTOQUE").insert({
        "nome_local": nome_local
    }).execute()

def listar_locais_estoque():
    return supabase.table("LOCAL_ESTOQUE").select("*").execute()
