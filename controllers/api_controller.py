from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    get_jwt_identity,
    get_jwt,
)

from models import db
import bcrypt

api_bp = Blueprint("api_bp", __name__)


# ---------- HELPERS ----------

def resposta_erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def require_admin():
    claims = get_jwt()  # pega os dados extras do token (claims)
    return claims.get("tipo_usuario") == 2


# ---------- AUTENTICAÇÃO ----------

@api_bp.route("/login", methods=["POST"])
def api_login():
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

    # identity como string (id do usuário)
    identity = str(user["id"])
    # claims extras com tipo e nome
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
    resp = db.listar_produtos()
    return jsonify(resp.data or []), 200


@api_bp.route("/produtos", methods=["POST"])
@jwt_required()
def api_criar_produto():
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

    resp = db.inserir_produto(
        dados["nome_produto"],
        float(dados["custo_produto_Unit"]),
        float(dados["valor_venda_Unit"]),
        int(dados["id_local"]),
        int(dados["id_categoria"]),
        int(dados["id_fornecedor"]),
        quantidade=quantidade,
        estoque_minimo=estoque_minimo,
    )
    return jsonify(resp.data or {}), 201


@api_bp.route("/produtos/<int:id_produto>", methods=["GET"])
@jwt_required()
def api_obter_produto(id_produto):
    resp = db.listar_produtos()
    itens = resp.data or []
    produto = next((p for p in itens if p["id"] == id_produto), None)
    if not produto:
        return resposta_erro("Produto não encontrado", 404)
    return jsonify(produto), 200


@api_bp.route("/produtos/<int:id_produto>", methods=["PUT"])
@jwt_required()
def api_atualizar_produto(id_produto):
    dados = request.get_json() or {}
    # aqui pode usar supabase diretamente ou criar função update no db.py
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
    dados = request.get_json() or {}
    qtd = int(dados.get("quantidade", 0))
    if qtd <= 0:
        return resposta_erro("Quantidade deve ser > 0", 400)

    try:
        db.entrada_estoque(id_produto, qtd)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    return jsonify({"mensagem": "Entrada registrada", "quantidade": qtd}), 200


@api_bp.route("/produtos/<int:id_produto>/saida", methods=["POST"])
@jwt_required()
def api_saida_estoque(id_produto):
    dados = request.get_json() or {}
    qtd = int(dados.get("quantidade", 0))
    if qtd <= 0:
        return resposta_erro("Quantidade deve ser > 0", 400)

    try:
        db.saida_estoque(id_produto, qtd)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    return jsonify({"mensagem": "Saída registrada", "quantidade": qtd}), 200


# ---------- CATEGORIAS / LOCAIS / FORNECEDORES (ADMIN) ----------

@api_bp.route("/categorias", methods=["GET"])
@jwt_required()
def api_listar_categorias():
    resp = db.listar_categorias()
    return jsonify(resp.data or []), 200


@api_bp.route("/categorias", methods=["POST"])
@jwt_required()
def api_criar_categoria():
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    dados = request.get_json() or {}
    nome = dados.get("nome_categoria")
    if not nome:
        return resposta_erro("nome_categoria é obrigatório", 400)

    resp = db.inserir_categoria(nome)
    return jsonify(resp.data or {}), 201


@api_bp.route("/categorias/<int:id_categoria>", methods=["DELETE"])
@jwt_required()
def api_deletar_categoria(id_categoria):
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    try:
        resp = db.deletar_categoria(id_categoria)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    if not resp.data:
        return resposta_erro("Categoria não encontrada", 404)
    return "", 204


# Locais e Fornecedores: padrão idêntico, usando funções já existentes do db

@api_bp.route("/locais", methods=["GET"])
@jwt_required()
def api_listar_locais():
    resp = db.listar_locais_estoque()
    return jsonify(resp.data or []), 200


@api_bp.route("/locais", methods=["POST"])
@jwt_required()
def api_criar_local():
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    dados = request.get_json() or {}
    nome = dados.get("nome_local")
    if not nome:
        return resposta_erro("nome_local é obrigatório", 400)

    resp = db.inserir_local_estoque(nome)
    return jsonify(resp.data or {}), 201


@api_bp.route("/locais/<int:id_local>", methods=["DELETE"])
@jwt_required()
def api_deletar_local(id_local):
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    try:
        resp = db.deletar_local_estoque(id_local)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    if not resp.data:
        return resposta_erro("Local não encontrado", 404)
    return "", 204


@api_bp.route("/fornecedores", methods=["GET"])
@jwt_required()
def api_listar_fornecedores():
    resp = db.listar_fornecedores()
    return jsonify(resp.data or []), 200


@api_bp.route("/fornecedores", methods=["POST"])
@jwt_required()
def api_criar_fornecedor():
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    dados = request.get_json() or {}
    nome = dados.get("nome_fornecedor")
    if not nome:
        return resposta_erro("nome_fornecedor é obrigatório", 400)

    resp = db.inserir_fornecedor(nome)
    return jsonify(resp.data or {}), 201


@api_bp.route("/fornecedores/<int:id_fornecedor>", methods=["DELETE"])
@jwt_required()
def api_deletar_fornecedor(id_fornecedor):
    if not require_admin():
        return resposta_erro("Acesso restrito a administradores", 403)

    try:
        resp = db.deletar_fornecedor(id_fornecedor)
    except ValueError as e:
        return resposta_erro(str(e), 400)
    if not resp.data:
        return resposta_erro("Fornecedor não encontrado", 404)
    return "", 204
