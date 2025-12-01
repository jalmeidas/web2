from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models import db

admin_bp = Blueprint("admin_bp", __name__)


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth_bp.login"))
        if session.get("user_tipo") != 2:  # 2 = administrador
            flash("Acesso permitido apenas para administradores.", "danger")
            return redirect(url_for("produtos_bp.index"))
        return view_func(*args, **kwargs)

    return wrapper


# ---------- FORNECEDORES ----------
@admin_bp.route("/fornecedores", methods=["GET", "POST"])
@admin_required
def fornecedores():
    if request.method == "POST":
        try:
            nome = request.form["nome_fornecedor"]
            db.inserir_fornecedor(nome)
            flash("Fornecedor cadastrado com sucesso!", "success")
            return redirect(url_for("admin_bp.fornecedores"))
        except Exception as e:
            flash(f"Erro ao cadastrar fornecedor: {e}", "danger")

    resp = db.listar_fornecedores()
    fornecedores = resp.data or []
    return render_template("fornecedores.html", fornecedores=fornecedores)


@admin_bp.route("/fornecedores/<int:id_fornecedor>/delete", methods=["POST"])
@admin_required
def deletar_fornecedor_view(id_fornecedor):
    try:
        db.deletar_fornecedor(id_fornecedor)
        flash("Fornecedor deletado.", "success")
    except ValueError as e:
        flash(str(e), "warning")
    return redirect(url_for("admin_bp.fornecedores"))


# ---------- LOCAIS ----------
@admin_bp.route("/locais", methods=["GET", "POST"])
@admin_required
def locais():
    if request.method == "POST":
        try:
            nome = request.form["nome_local"]
            db.inserir_local_estoque(nome)
            flash("Local criado com sucesso!", "success")
            return redirect(url_for("admin_bp.locais"))
        except Exception as e:
            flash(f"Erro ao criar local: {e}", "danger")

    resp = db.listar_locais_estoque()
    locais = resp.data or []
    return render_template("locais.html", locais=locais)


@admin_bp.route("/locais/<int:id_local>/delete", methods=["POST"])
@admin_required
def deletar_local(id_local):
    try:
        db.deletar_local_estoque(id_local)
        flash("Local deletado.", "success")
    except ValueError as e:
        flash(str(e), "warning")
    return redirect(url_for("admin_bp.locais"))


# ---------- CATEGORIAS ----------
@admin_bp.route("/categorias", methods=["GET", "POST"])
@admin_required
def categorias():
    if request.method == "POST":
        try:
            nome = request.form["nome_categoria"]
            db.inserir_categoria(nome)
            flash("Categoria criada com sucesso!", "success")
            return redirect(url_for("admin_bp.categorias"))
        except Exception as e:
            flash(f"Erro ao criar categoria: {e}", "danger")

    resp = db.listar_categorias()
    categorias = resp.data or []
    return render_template("categorias.html", categorias=categorias)


@admin_bp.route("/categorias/<int:id_categoria>/delete", methods=["POST"])
@admin_required
def deletar_categoria_view(id_categoria):
    try:
        db.deletar_categoria(id_categoria)
        flash("Categoria deletada.", "success")
    except ValueError as e:
        flash(str(e), "warning")
    return redirect(url_for("admin_bp.categorias"))
