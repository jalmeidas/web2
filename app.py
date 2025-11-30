from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from supabase import create_client
import bcrypt
import db
from functools import wraps

SUPABASE_URL = "https://xuaybixptiibbvgodjhi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1YXliaXhwdGlpYmJ2Z29kamhpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0NDE4NTcsImV4cCI6MjA4MDAxNzg1N30.4nbuZYOq9jPeOh_h9sthJ4odvQd83yTxe0YAIovCfd0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
db.set_supabase_client(supabase)

app = Flask(__name__)
app.secret_key = "chave-flask-simples"

# ---------- AUTH ----------
@app.route("/login", methods=["GET", "POST"])
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
            return redirect(url_for("login"))

        user = resp.data
        hash_no_banco = user["senha_usuario"].encode("utf-8")
        senha_bytes = senha.encode("utf-8")

        if bcrypt.checkpw(senha_bytes, hash_no_banco):
            session["user_id"] = user["id"]
            session["user_name"] = user["nome_usuario"]
            session["user_tipo"] = user["tipo_usuario"]
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("index"))
        else:
            flash("Senha inválida", "danger")
            return redirect(url_for("login"))

    try:
        resp_usuarios = db.listar_usuarios()
        usuarios = resp_usuarios.data or []
    except Exception:
        usuarios = []
    
    return render_template("login.html", usuarios=usuarios)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form["nome_usuario"]
        tipo = int(request.form.get("tipo_usuario", 1))
        senha = request.form["senha"]

        try:
            resp = db.buscar_usuario_por_nome(nome)
            if resp and resp.data:
                flash("Usuário já existe", "warning")
                return redirect(url_for("register"))
        except Exception:
            pass

        db.inserir_usuario(nome, tipo, senha)
        flash("Usuário cadastrado com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sessão.", "info")
    return redirect(url_for("login"))

# ---------- DECORATOR ----------
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper

# ---------- DASHBOARD ----------
@app.route("/")
@login_required
def index():
    return render_template("index.html")

# ---------- PRODUTOS ----------
@app.route("/produtos", methods=["GET", "POST"])
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

                db.inserir_produto(nome, custo, venda, id_local, id_categoria, id_fornecedor,
                                 quantidade=quantidade, estoque_minimo=estoque_minimo)
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
            
            return redirect(url_for("produtos"))
        
        except ValueError as e:
            flash(f"❌ {str(e)}", "danger")
        except Exception as e:
            flash(f"❌ Erro: {str(e)}", "danger")

    # GET: buscar TODOS os dados com JOIN
    resp_produtos = db.listar_produtos()
    resp_locais = db.listar_locais_estoque()
    resp_fornecedores = db.listar_fornecedores()
    resp_categorias = db.listar_categorias()
    
    produtos = resp_produtos.data or []
    locais = resp_locais.data or []
    fornecedores = resp_fornecedores.data or []
    categorias = resp_categorias.data or []
    
    # Dicionários para lookup rápido (ID → nome)
    locais_dict = {l['id']: l['nome_local'] for l in locais}
    fornecedores_dict = {f['id']: f['nome_fornecedor'] for f in fornecedores}
    categorias_dict = {c['id']: c['nome_categoria'] for c in categorias}
    
    # Enriquecer produtos com nomes
    for p in produtos:
        p['local_nome'] = locais_dict.get(p['id_local'], 'N/A')
        p['fornecedor_nome'] = fornecedores_dict.get(p['id_fornecedor'], 'N/A')
        p['categoria_nome'] = categorias_dict.get(p['id_categoria'], 'N/A')
    
    return render_template("produtos.html", 
                          produtos=produtos, 
                          locais=locais, 
                          fornecedores=fornecedores,
                          categorias=categorias)


@app.route("/produtos/<int:id_produto>/delete", methods=["POST"])
@login_required
def deletar_produto(id_produto):
    db.deletar_produto(id_produto)
    flash("Produto deletado.", "success")
    return redirect(url_for("produtos"))

# ---------- FORNECEDORES ----------
@app.route("/fornecedores", methods=["GET", "POST"])
@login_required
def fornecedores():
    if request.method == "POST":
        try:
            nome = request.form["nome_fornecedor"]
            db.inserir_fornecedor(nome)
            flash("Fornecedor cadastrado com sucesso!", "success")
            return redirect(url_for("fornecedores"))
        except Exception as e:
            flash(f"Erro ao cadastrar fornecedor: {e}", "danger")

    resp = db.listar_fornecedores()
    fornecedores = resp.data or []
    return render_template("fornecedores.html", fornecedores=fornecedores)

@app.route("/fornecedores/<int:id_fornecedor>/delete", methods=["POST"])
@login_required
def deletar_fornecedor_view(id_fornecedor):
    try:
        db.deletar_fornecedor(id_fornecedor)
        flash("Fornecedor deletado.", "success")
    except ValueError as e:
        flash(str(e), "warning")
    return redirect(url_for("fornecedores"))

# ---------- LOCAIS ----------
@app.route("/locais", methods=["GET", "POST"])
@login_required
def locais():
    if request.method == "POST":
        try:
            nome = request.form["nome_local"]
            db.inserir_local_estoque(nome)
            flash("Local criado com sucesso!", "success")
            return redirect(url_for("locais"))
        except Exception as e:
            flash(f"Erro ao criar local: {e}", "danger")

    resp = db.listar_locais_estoque()
    locais = resp.data or []
    return render_template("locais.html", locais=locais)

@app.route("/locais/<int:id_local>/delete", methods=["POST"])
@login_required
def deletar_local(id_local):
    try:
        db.deletar_local_estoque(id_local)
        flash("Local deletado.", "success")
    except ValueError as e:
        flash(str(e), "warning")
    return redirect(url_for("locais"))

# ---------- CATEGORIAS ----------
@app.route("/categorias", methods=["GET", "POST"])
@login_required
def categorias():
    if request.method == "POST":
        try:
            nome = request.form["nome_categoria"]
            db.inserir_categoria(nome)
            flash("Categoria criada com sucesso!", "success")
            return redirect(url_for("categorias"))
        except Exception as e:
            flash(f"Erro ao criar categoria: {e}", "danger")

    resp = db.listar_categorias()
    categorias = resp.data or []
    return render_template("categorias.html", categorias=categorias)

@app.route("/categorias/<int:id_categoria>/delete", methods=["POST"])
@login_required
def deletar_categoria_view(id_categoria):
    try:
        db.deletar_categoria(id_categoria)
        flash("Categoria deletada.", "success")
    except ValueError as e:
        flash(str(e), "warning")
    return redirect(url_for("categorias"))

if __name__ == "__main__":
    app.run(debug=True)
