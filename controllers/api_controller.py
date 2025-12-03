from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    get_jwt_identity,
    get_jwt,
)
from flasgger import swag_from

from models import db
import bcrypt

api_bp = Blueprint("api_bp", __name__)


# ---------- HELPERS ----------

def resposta_erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def require_admin():
    claims = get_jwt()
    return claims.get("tipo_usuario") == 2


# ---------- AUTENTICAÇÃO ----------

@api_bp.route("/login", methods=["POST"])
def api_login():
    """
    Endpoint de autenticação para obter token JWT
    ---
    tags:
      - Autenticação
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/LoginRequest'
    responses:
      200:
        description: Login realizado com sucesso
        schema:
          $ref: '#/definitions/LoginResponse'
        examples:
          application/json:
            access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      400:
        description: Campos obrigatórios ausentes
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Usuário não encontrado ou senha inválida
        schema:
          $ref: '#/definitions/Erro'
    """
    dados = request.get_json() or {}
    nome = dados.get("nome_usuario")
    senha = dados.get("senha")

    if not nome or not senha:
        return resposta_erro("nome_usuario e senha são obrigatórios", 400)

    try:
        resp = db.buscar_usuario_por_nome(nome)
    except Exception:
        resp = None

    if not resp or not resp.data:
        return resposta_erro("Usuário não encontrado", 401)

    user = resp.data
    hash_no_banco = user["senha_usuario"].encode("utf-8")
    if not bcrypt.checkpw(senha.encode("utf-8"), hash_no_banco):
        return resposta_erro("Credenciais inválidas", 401)

    identity = str(user["id"])
    additional_claims = {
        "nome_usuario": user["nome_usuario"],
        "tipo_usuario": user["tipo_usuario"],
    }

    token = create_access_token(identity=identity, additional_claims=additional_claims)
    return jsonify({"access_token": token}), 200


# ---------- PRODUTOS (CRUD + REGRA DE NEGÓCIO) ----------

@api_bp.route("/produtos", methods=["GET"])
@jwt_required()
def api_listar_produtos():
    """
    Lista todos os produtos cadastrados
    ---
    tags:
      - Produtos
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de produtos retornada com sucesso
        schema:
          type: array
          items:
            $ref: '#/definitions/Produto'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
    """
    resp = db.listar_produtos()
    return jsonify(resp.data or []), 200


@api_bp.route("/produtos", methods=["POST"])
@jwt_required()
def api_criar_produto():
    """
    Cria um novo produto com validações de estoque
    ---
    tags:
      - Produtos
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        description: Dados do produto a ser criado
        schema:
          $ref: '#/definitions/ProdutoInput'
    responses:
      201:
        description: Produto criado com sucesso
        schema:
          $ref: '#/definitions/Produto'
      400:
        description: Campos obrigatórios faltando ou validação de estoque
        schema:
          $ref: '#/definitions/Erro'
        examples:
          application/json:
            erro: "Quantidade inicial (5) não pode ser menor que o estoque mínimo (10)"
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
    """
    dados = request.get_json() or {}
    campos_obrig = [
        "nome_produto",
        "custo_produto_Unit",
        "valor_venda_Unit",
        "id_local",
        "id_categoria",
        "id_fornecedor",
    ]
    if not all(c in dados for c in campos_obrig):
        return resposta_erro("Campos obrigatórios faltando em produto", 400)

    quantidade = int(dados.get("quantidade", 0))
    estoque_minimo = int(dados.get("estoque_minimo", 0))
    estoque_maximo = int(dados.get("estoque_maximo", 999999))  # NOVO CAMPO
    id_usuario = int(get_jwt_identity())  # Pega ID do usuário do token JWT

    try:
        resp = db.inserir_produto(
            dados["nome_produto"],
            float(dados["custo_produto_Unit"]),
            float(dados["valor_venda_Unit"]),
            int(dados["id_local"]),
            int(dados["id_categoria"]),
            int(dados["id_fornecedor"]),
            quantidade=quantidade,
            estoque_minimo=estoque_minimo,
            estoque_maximo=estoque_maximo,  # NOVO CAMPO
            id_usuario=id_usuario,  # NOVO CAMPO
        )
        return jsonify(resp.data or {}), 201
    except ValueError as e:
        return resposta_erro(str(e), 400)


@api_bp.route("/produtos/<int:id_produto>", methods=["GET"])
@jwt_required()
def api_obter_produto(id_produto):
    """
    Obtém um produto específico por ID
    ---
    tags:
      - Produtos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_produto
        type: integer
        required: true
        description: ID do produto
        example: 1
    responses:
      200:
        description: Produto encontrado
        schema:
          $ref: '#/definitions/Produto'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Produto não encontrado
        schema:
          $ref: '#/definitions/Erro'
    """
    resp = db.listar_produtos()
    itens = resp.data or []
    produto = next((p for p in itens if p["id"] == id_produto), None)
    if not produto:
        return resposta_erro("Produto não encontrado", 404)
    return jsonify(produto), 200


@api_bp.route("/produtos/<int:id_produto>", methods=["PUT"])
@jwt_required()
def api_atualizar_produto(id_produto):
    """
    Atualiza os dados de um produto existente
    ---
    tags:
      - Produtos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_produto
        type: integer
        required: true
        description: ID do produto a ser atualizado
        example: 1
      - in: body
        name: body
        required: true
        description: Campos a serem atualizados (todos opcionais)
        schema:
          type: object
          properties:
            nome_produto:
              type: string
              example: "Caixa Isopor Grande"
            custo_produto_Unit:
              type: number
              format: float
              example: 6.0
            valor_venda_Unit:
              type: number
              format: float
              example: 12.0
            id_local:
              type: integer
              example: 1
            id_categoria:
              type: integer
              example: 1
            id_fornecedor:
              type: integer
              example: 1
            quantidade:
              type: integer
              example: 50
            estoque_minimo:
              type: integer
              example: 5
            estoque_maximo:
              type: integer
              example: 500
    responses:
      200:
        description: Produto atualizado com sucesso
        schema:
          $ref: '#/definitions/Produto'
      400:
        description: Nada para atualizar
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Produto não encontrado
        schema:
          $ref: '#/definitions/Erro'
    """
    dados = request.get_json() or {}
    update = {}
    for campo in [
        "nome_produto",
        "custo_produto_Unit",
        "valor_venda_Unit",
        "id_local",
        "id_categoria",
        "id_fornecedor",
        "quantidade",
        "estoque_minimo",
        "estoque_maximo",  # NOVO CAMPO
    ]:
        if campo in dados:
            update[campo] = dados[campo]

    if not update:
        return resposta_erro("Nada para atualizar", 400)

    resp = (
        db.supabase.table("PRODUTOS")
        .update(update)
        .eq("id", id_produto)
        .execute()
    )
    if not resp.data:
        return resposta_erro("Produto não encontrado", 404)
    return jsonify(resp.data[0]), 200


@api_bp.route("/produtos/<int:id_produto>", methods=["DELETE"])
@jwt_required()
def api_deletar_produto(id_produto):
    """
    Deleta um produto
    ---
    tags:
      - Produtos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_produto
        type: integer
        required: true
        description: ID do produto a ser deletado
        example: 1
    responses:
      204:
        description: Produto deletado com sucesso
      400:
        description: Erro ao deletar produto
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Produto não encontrado
        schema:
          $ref: '#/definitions/Erro'
    """
    try:
        resp = db.deletar_produto(id_produto)
    except Exception as e:
        return resposta_erro(str(e), 400)
    if not resp.data:
        return resposta_erro("Produto não encontrado", 404)
    return "", 204


# ---------- ENTRADA / SAÍDA (REGRA DE NEGÓCIO) ----------

@api_bp.route("/produtos/<int:id_produto>/entrada", methods=["POST"])
@jwt_required()
def api_entrada_estoque(id_produto):
    """
    Registra entrada de estoque (aumenta quantidade)
    Valida estoque máximo - não permite ultrapassar
    ---
    tags:
      - Estoque
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_produto
        type: integer
        required: true
        description: ID do produto
        example: 1
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/MovimentacaoEstoque'
    responses:
      200:
        description: Entrada registrada com sucesso
        schema:
          $ref: '#/definitions/MovimentacaoResponse'
        examples:
          application/json:
            mensagem: "Entrada registrada"
            quantidade: 10
      400:
        description: Quantidade inválida, produto não encontrado ou estoque máximo excedido
        schema:
          $ref: '#/definitions/Erro'
        examples:
          application/json:
            erro: "Entrada negada! Estoque máximo do produto 'Caixa Isopor' é 500. Estoque atual: 480. Tentativa de entrada: 30. Estoque resultante seria: 510."
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
    """
    dados = request.get_json() or {}
    qtd = int(dados.get("quantidade", 0))
    if qtd <= 0:
        return resposta_erro("Quantidade deve ser > 0", 400)

    id_usuario = int(get_jwt_identity())  # Pega ID do usuário do token JWT

    try:
        db.entrada_estoque(id_produto, qtd, id_usuario)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    return jsonify({"mensagem": "Entrada registrada", "quantidade": qtd}), 200


@api_bp.route("/produtos/<int:id_produto>/saida", methods=["POST"])
@jwt_required()
def api_saida_estoque(id_produto):
    """
    Registra saída de estoque (reduz quantidade)
    Valida estoque mínimo - não permite ficar abaixo do mínimo estabelecido
    ---
    tags:
      - Estoque
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_produto
        type: integer
        required: true
        description: ID do produto
        example: 1
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/MovimentacaoEstoque'
    responses:
      200:
        description: Saída registrada com sucesso
        schema:
          $ref: '#/definitions/MovimentacaoResponse'
        examples:
          application/json:
            mensagem: "Saída registrada"
            quantidade: 5
      400:
        description: Estoque insuficiente, quantidade inválida, estoque mínimo violado ou produto não encontrado
        schema:
          $ref: '#/definitions/Erro'
        examples:
          application/json:
            erro: "Saída negada! Estoque mínimo do produto 'Caixa Isopor' é 10. Estoque atual: 15. Tentativa de saída: 8. Estoque resultante seria: 7."
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
    """
    dados = request.get_json() or {}
    qtd = int(dados.get("quantidade", 0))
    if qtd <= 0:
        return resposta_erro("Quantidade deve ser > 0", 400)

    id_usuario = int(get_jwt_identity())  # Pega ID do usuário do token JWT

    try:
        db.saida_estoque(id_produto, qtd, id_usuario)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    return jsonify({"mensagem": "Saída registrada", "quantidade": qtd}), 200


# ---------- CATEGORIAS / LOCAIS / FORNECEDORES (ADMIN) ----------

@api_bp.route("/categorias", methods=["GET"])
@jwt_required()
def api_listar_categorias():
    """
    Lista todas as categorias
    ---
    tags:
      - Categorias
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de categorias retornada com sucesso
        schema:
          type: array
          items:
            $ref: '#/definitions/Categoria'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
    """
    resp = db.listar_categorias()
    return jsonify(resp.data or []), 200


@api_bp.route("/categorias", methods=["POST"])
@jwt_required()
def api_criar_categoria():
    """
    Cria uma nova categoria (apenas administradores)
    ---
    tags:
      - Categorias
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nome_categoria
          properties:
            nome_categoria:
              type: string
              example: "Alimentos"
    responses:
      201:
        description: Categoria criada com sucesso
        schema:
          $ref: '#/definitions/Categoria'
      400:
        description: nome_categoria é obrigatório
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      403:
        description: Acesso restrito a administradores
        schema:
          $ref: '#/definitions/Erro'
    """
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    dados = request.get_json() or {}
    nome = dados.get("nome_categoria")
    if not nome:
        return resposta_erro("nome_categoria é obrigatório", 400)

    resp = db.inserir_categoria(nome)
    return jsonify(resp.data or {}), 201


@api_bp.route("/categorias/<int:id_categoria>", methods=["GET"])
@jwt_required()
def api_obter_categoria(id_categoria):
    """
    Obtém uma categoria específica por ID
    ---
    tags:
      - Categorias
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_categoria
        type: integer
        required: true
        description: ID da categoria
        example: 1
    responses:
      200:
        description: Categoria encontrada
        schema:
          $ref: '#/definitions/Categoria'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Categoria não encontrada
        schema:
          $ref: '#/definitions/Erro'
    """
    resp = db.listar_categorias()
    categorias = resp.data or []
    categoria = next((c for c in categorias if c["id"] == id_categoria), None)
    if not categoria:
        return resposta_erro("Categoria não encontrada", 404)
    return jsonify(categoria), 200


@api_bp.route("/categorias/<int:id_categoria>", methods=["PUT"])
@jwt_required()
def api_atualizar_categoria(id_categoria):
    """
    Atualiza uma categoria (apenas administradores)
    ---
    tags:
      - Categorias
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_categoria
        type: integer
        required: true
        description: ID da categoria a ser atualizada
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nome_categoria
          properties:
            nome_categoria:
              type: string
              example: "Eletrônicos"
    responses:
      200:
        description: Categoria atualizada com sucesso
        schema:
          $ref: '#/definitions/Categoria'
      400:
        description: nome_categoria é obrigatório
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      403:
        description: Acesso restrito a administradores
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Categoria não encontrada
        schema:
          $ref: '#/definitions/Erro'
    """
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    dados = request.get_json() or {}
    nome = dados.get("nome_categoria")
    if not nome:
        return resposta_erro("nome_categoria é obrigatório", 400)

    resp = (
        db.supabase.table("CATEGORIA")
        .update({"nome_categoria": nome})
        .eq("id", id_categoria)
        .execute()
    )
    if not resp.data:
        return resposta_erro("Categoria não encontrada", 404)
    return jsonify(resp.data[0]), 200


@api_bp.route("/categorias/<int:id_categoria>", methods=["DELETE"])
@jwt_required()
def api_deletar_categoria(id_categoria):
    """
    Deleta uma categoria (apenas administradores)
    Não permite deletar se houver produtos usando a categoria
    ---
    tags:
      - Categorias
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_categoria
        type: integer
        required: true
        description: ID da categoria a ser deletada
        example: 1
    responses:
      204:
        description: Categoria deletada com sucesso
      400:
        description: Existem produtos usando esta categoria
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      403:
        description: Acesso restrito a administradores
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Categoria não encontrada
        schema:
          $ref: '#/definitions/Erro'
    """
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    try:
        resp = db.deletar_categoria(id_categoria)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    if not resp.data:
        return resposta_erro("Categoria não encontrada", 404)
    return "", 204


# ---------- LOCAIS DE ESTOQUE ----------

@api_bp.route("/locais", methods=["GET"])
@jwt_required()
def api_listar_locais():
    """
    Lista todos os locais de estoque
    ---
    tags:
      - Locais
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de locais retornada com sucesso
        schema:
          type: array
          items:
            $ref: '#/definitions/LocalEstoque'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
    """
    resp = db.listar_locais_estoque()
    return jsonify(resp.data or []), 200


@api_bp.route("/locais", methods=["POST"])
@jwt_required()
def api_criar_local():
    """
    Cria um novo local de estoque (apenas administradores)
    ---
    tags:
      - Locais
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nome_local
          properties:
            nome_local:
              type: string
              example: "Matriz"
    responses:
      201:
        description: Local criado com sucesso
        schema:
          $ref: '#/definitions/LocalEstoque'
      400:
        description: nome_local é obrigatório
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      403:
        description: Acesso restrito a administradores
        schema:
          $ref: '#/definitions/Erro'
    """
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    dados = request.get_json() or {}
    nome = dados.get("nome_local")
    if not nome:
        return resposta_erro("nome_local é obrigatório", 400)

    resp = db.inserir_local_estoque(nome)
    return jsonify(resp.data or {}), 201


@api_bp.route("/locais/<int:id_local>", methods=["GET"])
@jwt_required()
def api_obter_local(id_local):
    """
    Obtém um local específico por ID
    ---
    tags:
      - Locais
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_local
        type: integer
        required: true
        description: ID do local
        example: 1
    responses:
      200:
        description: Local encontrado
        schema:
          $ref: '#/definitions/LocalEstoque'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Local não encontrado
        schema:
          $ref: '#/definitions/Erro'
    """
    resp = db.listar_locais_estoque()
    locais = resp.data or []
    local = next((l for l in locais if l["id"] == id_local), None)
    if not local:
        return resposta_erro("Local não encontrado", 404)
    return jsonify(local), 200


@api_bp.route("/locais/<int:id_local>", methods=["PUT"])
@jwt_required()
def api_atualizar_local(id_local):
    """
    Atualiza um local de estoque (apenas administradores)
    ---
    tags:
      - Locais
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_local
        type: integer
        required: true
        description: ID do local a ser atualizado
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nome_local
          properties:
            nome_local:
              type: string
              example: "Filial Sul"
    responses:
      200:
        description: Local atualizado com sucesso
        schema:
          $ref: '#/definitions/LocalEstoque'
      400:
        description: nome_local é obrigatório
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      403:
        description: Acesso restrito a administradores
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Local não encontrado
        schema:
          $ref: '#/definitions/Erro'
    """
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    dados = request.get_json() or {}
    nome = dados.get("nome_local")
    if not nome:
        return resposta_erro("nome_local é obrigatório", 400)

    resp = (
        db.supabase.table("LOCAL_ESTOQUE")
        .update({"nome_local": nome})
        .eq("id", id_local)
        .execute()
    )
    if not resp.data:
        return resposta_erro("Local não encontrado", 404)
    return jsonify(resp.data[0]), 200


@api_bp.route("/locais/<int:id_local>", methods=["DELETE"])
@jwt_required()
def api_deletar_local(id_local):
    """
    Deleta um local de estoque (apenas administradores)
    Não permite deletar se houver produtos neste local
    ---
    tags:
      - Locais
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_local
        type: integer
        required: true
        description: ID do local a ser deletado
        example: 1
    responses:
      204:
        description: Local deletado com sucesso
      400:
        description: Existem produtos cadastrados neste local
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      403:
        description: Acesso restrito a administradores
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Local não encontrado
        schema:
          $ref: '#/definitions/Erro'
    """
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    try:
        resp = db.deletar_local_estoque(id_local)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    if not resp.data:
        return resposta_erro("Local não encontrado", 404)
    return "", 204


# ---------- FORNECEDORES ----------

@api_bp.route("/fornecedores", methods=["GET"])
@jwt_required()
def api_listar_fornecedores():
    """
    Lista todos os fornecedores
    ---
    tags:
      - Fornecedores
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de fornecedores retornada com sucesso
        schema:
          type: array
          items:
            $ref: '#/definitions/Fornecedor'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
    """
    resp = db.listar_fornecedores()
    return jsonify(resp.data or []), 200


@api_bp.route("/fornecedores", methods=["POST"])
@jwt_required()
def api_criar_fornecedor():
    """
    Cria um novo fornecedor (apenas administradores)
    ---
    tags:
      - Fornecedores
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nome_fornecedor
          properties:
            nome_fornecedor:
              type: string
              example: "Fornecedor X"
    responses:
      201:
        description: Fornecedor criado com sucesso
        schema:
          $ref: '#/definitions/Fornecedor'
      400:
        description: nome_fornecedor é obrigatório
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      403:
        description: Acesso restrito a administradores
        schema:
          $ref: '#/definitions/Erro'
    """
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    dados = request.get_json() or {}
    nome = dados.get("nome_fornecedor")
    if not nome:
        return resposta_erro("nome_fornecedor é obrigatório", 400)

    resp = db.inserir_fornecedor(nome)
    return jsonify(resp.data or {}), 201


@api_bp.route("/fornecedores/<int:id_fornecedor>", methods=["GET"])
@jwt_required()
def api_obter_fornecedor(id_fornecedor):
    """
    Obtém um fornecedor específico por ID
    ---
    tags:
      - Fornecedores
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_fornecedor
        type: integer
        required: true
        description: ID do fornecedor
        example: 1
    responses:
      200:
        description: Fornecedor encontrado
        schema:
          $ref: '#/definitions/Fornecedor'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Fornecedor não encontrado
        schema:
          $ref: '#/definitions/Erro'
    """
    resp = db.listar_fornecedores()
    fornecedores = resp.data or []
    fornecedor = next((f for f in fornecedores if f["id"] == id_fornecedor), None)
    if not fornecedor:
        return resposta_erro("Fornecedor não encontrado", 404)
    return jsonify(fornecedor), 200


@api_bp.route("/fornecedores/<int:id_fornecedor>", methods=["PUT"])
@jwt_required()
def api_atualizar_fornecedor(id_fornecedor):
    """
    Atualiza um fornecedor (apenas administradores)
    ---
    tags:
      - Fornecedores
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_fornecedor
        type: integer
        required: true
        description: ID do fornecedor a ser atualizado
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nome_fornecedor
          properties:
            nome_fornecedor:
              type: string
              example: "Fornecedor ABC Ltda"
    responses:
      200:
        description: Fornecedor atualizado com sucesso
        schema:
          $ref: '#/definitions/Fornecedor'
      400:
        description: nome_fornecedor é obrigatório
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      403:
        description: Acesso restrito a administradores
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Fornecedor não encontrado
        schema:
          $ref: '#/definitions/Erro'
    """
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    dados = request.get_json() or {}
    nome = dados.get("nome_fornecedor")
    if not nome:
        return resposta_erro("nome_fornecedor é obrigatório", 400)

    resp = (
        db.supabase.table("FORNECEDOR")
        .update({"nome_fornecedor": nome})
        .eq("id", id_fornecedor)
        .execute()
    )
    if not resp.data:
        return resposta_erro("Fornecedor não encontrado", 404)
    return jsonify(resp.data[0]), 200


@api_bp.route("/fornecedores/<int:id_fornecedor>", methods=["DELETE"])
@jwt_required()
def api_deletar_fornecedor(id_fornecedor):
    """
    Deleta um fornecedor (apenas administradores)
    Não permite deletar se houver produtos vinculados ao fornecedor
    ---
    tags:
      - Fornecedores
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_fornecedor
        type: integer
        required: true
        description: ID do fornecedor a ser deletado
        example: 1
    responses:
      204:
        description: Fornecedor deletado com sucesso
      400:
        description: Existem produtos vinculados a este fornecedor
        schema:
          $ref: '#/definitions/Erro'
      401:
        description: Token JWT ausente ou inválido
        schema:
          $ref: '#/definitions/Erro'
      403:
        description: Acesso restrito a administradores
        schema:
          $ref: '#/definitions/Erro'
      404:
        description: Fornecedor não encontrado
        schema:
          $ref: '#/definitions/Erro'
    """
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    try:
        resp = db.deletar_fornecedor(id_fornecedor)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    if not resp.data:
        return resposta_erro("Fornecedor não encontrado", 404)
    return "", 204
