from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import bcrypt
from models import db

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nome = request.form["nome_usuario"]
        senha = request.form["senha"]

        try:
            resp = db.buscar_usuario_por_nome(nome)
        except Exception:
            resp = None

        if not resp or not resp.data:
            flash("Usuário não encontrado", "danger")
            return redirect(url_for("auth_bp.login"))

        user = resp.data
        hash_no_banco = user["senha_usuario"].encode("utf-8")
        senha_bytes = senha.encode("utf-8")

        if bcrypt.checkpw(senha_bytes, hash_no_banco):
            session["user_id"] = user["id"]
            session["user_name"] = user["nome_usuario"]
            session["user_tipo"] = user["tipo_usuario"]
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("produtos_bp.index"))
        else:
            flash("Senha inválida", "danger")
            return redirect(url_for("auth_bp.login"))

    try:
        resp_usuarios = db.listar_usuarios()
        usuarios = resp_usuarios.data or []
    except Exception:
        usuarios = []
    
    return render_template("login.html", usuarios=usuarios)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form["nome_usuario"]
        tipo = int(request.form.get("tipo_usuario", 1))
        senha = request.form["senha"]

        try:
            resp = db.buscar_usuario_por_nome(nome)
            if resp and resp.data:
                flash("Usuário já existe", "warning")
                return redirect(url_for("auth_bp.register"))
        except Exception:
            pass

        db.inserir_usuario(nome, tipo, senha)
        flash("Usuário cadastrado com sucesso! Faça login.", "success")
        return redirect(url_for("auth_bp.login"))

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sessão.", "info")
    return redirect(url_for("auth_bp.login"))
