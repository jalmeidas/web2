
from flask import Flask
from supabase import create_client
from models import db
from controllers.auth_controller import auth_bp
from controllers.produtos_controller import produtos_bp
from controllers.admin_controller import admin_bp

SUPABASE_URL = "https://xuaybixptiibbvgodjhi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1YXliaXhwdGlpYmJ2Z29kamhpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0NDE4NTcsImV4cCI6MjA4MDAxNzg1N30.4nbuZYOq9jPeOh_h9sthJ4odvQd83yTxe0YAIovCfd0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
db.set_supabase_client(supabase)

app = Flask(__name__)
app.secret_key = "chave-flask-simples"

app.register_blueprint(auth_bp)
app.register_blueprint(produtos_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True)
