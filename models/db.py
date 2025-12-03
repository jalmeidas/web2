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
                    quantidade=0, estoque_minimo=0, estoque_maximo=999999, id_usuario=None):
    """
    Insere um novo produto com validação de estoque.
    
    Args:
        estoque_minimo: Quantidade mínima permitida em estoque
        estoque_maximo: Quantidade máxima permitida em estoque
        quantidade: Quantidade inicial (deve estar entre mínimo e máximo)
        id_usuario: ID do usuário que está cadastrando (para registro de movimento)
    """
    # Validação: quantidade inicial não pode ser menor que o mínimo
    if quantidade < estoque_minimo:
        raise ValueError(f"Quantidade inicial ({quantidade}) não pode ser menor que o estoque mínimo ({estoque_minimo})")
    
    # Validação: quantidade inicial não pode ser maior que o máximo
    if quantidade > estoque_maximo:
        raise ValueError(f"Quantidade inicial ({quantidade}) não pode ser maior que o estoque máximo ({estoque_maximo})")
    
    # Validação: mínimo não pode ser maior que máximo
    if estoque_minimo > estoque_maximo:
        raise ValueError(f"Estoque mínimo ({estoque_minimo}) não pode ser maior que o estoque máximo ({estoque_maximo})")
    
    resp = supabase.table("PRODUTOS").insert({
        "nome_produto": nome_produto,
        "custo_produto_Unit": custo_produto_Unit,
        "valor_venda_Unit": valor_venda_Unit,
        "id_local": id_local,
        "id_categoria": id_categoria,
        "id_fornecedor": id_fornecedor,
        "quantidade": quantidade,
        "estoque_minimo": estoque_minimo,
        "estoque_maximo": estoque_maximo,
    }).execute()
    
    # Registrar movimento inicial se quantidade > 0 e usuário informado
    if quantidade > 0 and id_usuario:
        id_produto_novo = resp.data[0]["id"]
        registrar_movimento(id_produto_novo, id_usuario, "ENTRADA", quantidade)
    
    return resp



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


def registrar_movimento(id_produto, id_usuario, tipo_movimento, quantidade):
    """
    Registra movimento de estoque na tabela MOVIMENTO_ESTOQUE.
    
    Args:
        id_produto: ID do produto
        id_usuario: ID do usuário que realizou o movimento
        tipo_movimento: 'ENTRADA' ou 'SAIDA'
        quantidade: Quantidade movimentada
    """
    return supabase.table("MOVIMENTO_ESTOQUE").insert({
        "id_produto": id_produto,
        "id_usuario": id_usuario,
        "tipo_movimento": tipo_movimento,
        "quantidade": quantidade,
    }).execute()


# READ

def listar_usuarios():
    return supabase.table("USUARIOS").select("*").execute()


def listar_locais_estoque():
    return supabase.table("LOCAL_ESTOQUE").select("*").execute()


def listar_produtos():
    return supabase.table("PRODUTOS").select("*").execute()


def listar_fornecedores():
    return supabase.table("FORNECEDOR").select("*").execute()


# UPDATE (estoque) - COM VALIDAÇÕES MELHORADAS

def entrada_estoque(id_produto, quantidade, id_usuario=None):
    """
    Registra entrada de estoque com validação de estoque máximo.
    
    Regras:
    - Quantidade de entrada deve ser > 0
    - Estoque após entrada não pode ultrapassar estoque_maximo
    """
    if quantidade <= 0:
        raise ValueError("Quantidade de entrada deve ser maior que zero")
    
    produto_resp = (
        supabase.table("PRODUTOS")
        .select("quantidade, estoque_maximo, nome_produto")
        .eq("id", id_produto)
        .single()
        .execute()
    )
    if not produto_resp.data:
        raise ValueError("Produto não encontrado")

    quantidade_atual = produto_resp.data["quantidade"]
    estoque_maximo = produto_resp.data.get("estoque_maximo", 999999)
    nome_produto = produto_resp.data.get("nome_produto", "")
    
    nova_quantidade = quantidade_atual + quantidade
    
    # VALIDAÇÃO: não permitir estoque acima do máximo
    if nova_quantidade > estoque_maximo:
        raise ValueError(
            f"Entrada negada! Estoque máximo do produto '{nome_produto}' é {estoque_maximo}. "
            f"Estoque atual: {quantidade_atual}. "
            f"Tentativa de entrada: {quantidade}. "
            f"Estoque resultante seria: {nova_quantidade}."
        )

    resp = (
        supabase.table("PRODUTOS")
        .update({"quantidade": nova_quantidade})
        .eq("id", id_produto)
        .execute()
    )
    
    # Registrar movimento
    if id_usuario:
        registrar_movimento(id_produto, id_usuario, "ENTRADA", quantidade)
    
    # Alerta se estiver próximo do máximo (80% ou mais)
    percentual = (nova_quantidade / estoque_maximo) * 100
    if percentual >= 80:
        print(f"⚠️ ATENÇÃO: Estoque de '{nome_produto}' está em {percentual:.1f}% da capacidade máxima!")
    
    return resp


def saida_estoque(id_produto, quantidade, id_usuario=None):
    """
    Registra saída de estoque com validação de estoque mínimo.
    
    Regras:
    - Quantidade de saída deve ser > 0
    - Estoque não pode ficar negativo
    - Estoque após saída não pode ficar abaixo do estoque_minimo
    """
    if quantidade <= 0:
        raise ValueError("Quantidade de saída deve ser maior que zero")
    
    produto_resp = (
        supabase.table("PRODUTOS")
        .select("quantidade, estoque_minimo, nome_produto")
        .eq("id", id_produto)
        .single()
        .execute()
    )
    if not produto_resp.data:
        raise ValueError("Produto não encontrado")

    quantidade_atual = produto_resp.data["quantidade"]
    estoque_minimo = produto_resp.data.get("estoque_minimo", 0)
    nome_produto = produto_resp.data.get("nome_produto", "")

    # VALIDAÇÃO 1: estoque não pode ficar negativo
    if quantidade_atual < quantidade:
        raise ValueError(
            f"Estoque insuficiente! "
            f"Produto '{nome_produto}' tem apenas {quantidade_atual} unidades. "
            f"Tentativa de saída: {quantidade}."
        )

    nova_quantidade = quantidade_atual - quantidade
    
    # VALIDAÇÃO 2: não permitir estoque abaixo do mínimo
    if nova_quantidade < estoque_minimo:
        raise ValueError(
            f"Saída negada! Estoque mínimo do produto '{nome_produto}' é {estoque_minimo}. "
            f"Estoque atual: {quantidade_atual}. "
            f"Tentativa de saída: {quantidade}. "
            f"Estoque resultante seria: {nova_quantidade}."
        )
    
    resp = (
        supabase.table("PRODUTOS")
        .update({"quantidade": nova_quantidade})
        .eq("id", id_produto)
        .execute()
    )

    # Registrar movimento
    if id_usuario:
        registrar_movimento(id_produto, id_usuario, "SAIDA", quantidade)

    # Alerta se estiver próximo do mínimo (até 120% do mínimo)
    if nova_quantidade <= estoque_minimo * 1.2:
        print(f"⚠️ ATENÇÃO: Estoque de '{nome_produto}' está próximo do mínimo! Atual: {nova_quantidade}, Mínimo: {estoque_minimo}")

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
