from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models import db

produtos_bp = Blueprint("produtos_bp", __name__)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth_bp.login"))
        return view_func(*args, **kwargs)

    return wrapper


@produtos_bp.route("/")
@login_required
def index():
    return render_template("index.html")


@produtos_bp.route("/produtos", methods=["GET", "POST"])
@login_required
def produtos():
    if request.method == "POST":
        try:
            # CADASTRO NOVO PRODUTO
            if "nome_produto" in request.form:
                nome = request.form["nome_produto"]
                custo = float(request.form["custo"])
                venda = float(request.form["venda"])
                id_local = int(request.form["id_local"])
                id_categoria = int(request.form["id_categoria"])
                id_fornecedor = int(request.form["id_fornecedor"])
                quantidade = int(request.form.get("quantidade", 0))
                estoque_minimo = int(request.form.get("estoque_minimo", 0))

                db.inserir_produto(
                    nome,
                    custo,
                    venda,
                    id_local,
                    id_categoria,
                    id_fornecedor,
                    quantidade=quantidade,
                    estoque_minimo=estoque_minimo,
                )
                flash("✅ Produto criado!", "success")

            # MOVIMENTAÇÃO DE ESTOQUE
            elif "acao" in request.form:
                id_produto = int(request.form["id_produto"])
                acao = request.form["acao"]

                if acao == "entrada":
                    qtd = int(request.form["quantidade_entrada"])
                    db.entrada_estoque(id_produto, qtd)
                    flash(f"✅ +{qtd} unidades!", "success")
                elif acao == "saida":
                    qtd = int(request.form["quantidade_saida"])
                    db.saida_estoque(id_produto, qtd)
                    flash(f"✅ -{qtd} unidades!", "success")

            return redirect(url_for("produtos_bp.produtos"))

        except ValueError as e:
            flash(f"❌ {str(e)}", "danger")
        except Exception as e:
            flash(f"❌ Erro: {str(e)}", "danger")

    # GET: buscar dados
    resp_produtos = db.listar_produtos()
    resp_locais = db.listar_locais_estoque()
    resp_fornecedores = db.listar_fornecedores()
    resp_categorias = db.listar_categorias()

    produtos = resp_produtos.data or []
    locais = resp_locais.data or []
    fornecedores = resp_fornecedores.data or []
    categorias = resp_categorias.data or []

    # Dicionários para mostrar nomes
    locais_dict = {l["id"]: l["nome_local"] for l in locais}
    fornecedores_dict = {f["id"]: f["nome_fornecedor"] for f in fornecedores}
    categorias_dict = {c["id"]: c["nome_categoria"] for c in categorias}

    for p in produtos:
        p["local_nome"] = locais_dict.get(p["id_local"], "N/A")
        p["fornecedor_nome"] = fornecedores_dict.get(p["id_fornecedor"], "N/A")
        p["categoria_nome"] = categorias_dict.get(p["id_categoria"], "N/A")

    return render_template(
        "produtos.html",
        produtos=produtos,
        locais=locais,
        fornecedores=fornecedores,
        categorias=categorias,
    )


@produtos_bp.route("/produtos/<int:id_produto>/delete", methods=["POST"])
@login_required
def deletar_produto(id_produto):
    db.deletar_produto(id_produto)
    flash("Produto deletado.", "success")
    return redirect(url_for("produtos_bp.produtos"))
