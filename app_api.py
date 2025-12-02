from flask import Flask
from supabase import create_client
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from models import db
from controllers.api_controller import api_bp
from swagger_config import swagger_config, swagger_template

SUPABASE_URL = "https://xuaybixptiibbvgodjhi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1YXliaXhwdGlpYmJ2Z29kamhpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0NDE4NTcsImV4cCI6MjA4MDAxNzg1N30.4nbuZYOq9jPeOh_h9sthJ4odvQd83yTxe0YAIovCfd0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
db.set_supabase_client(supabase)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "chaveapi123"
jwt = JWTManager(app)

# Configurar Swagger
swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Registrar blueprint da API
app.register_blueprint(api_bp, url_prefix="/api")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 API de Estoque iniciada!")
    print("="*60)
    print("📍 API rodando em: http://localhost:5001/api")
    print("📚 Documentação Swagger: http://localhost:5001/swagger")
    print("="*60 + "\n")
    app.run(port=5001, debug=True)
