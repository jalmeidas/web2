"""
Configuração do Swagger/OpenAPI para a API de Estoque
"""

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/",
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "API de Gestão de Estoque",
        "description": """
API completa para gestão de estoque com autenticação JWT.

## Funcionalidades principais:
- **Autenticação JWT** - Login seguro com token
- **Gestão de Produtos** - CRUD completo de produtos
- **Controle de Estoque** - Entrada e saída de produtos com validação
- **Categorias, Locais e Fornecedores** - Gerenciamento auxiliar
- **Controle de Acesso** - Operador e Administrador

## Tipos de Usuário:
- **Operador (tipo_usuario = 1)**: Pode listar dados e fazer movimentações de estoque
- **Administrador (tipo_usuario = 2)**: Acesso total, incluindo CRUD de todas as entidades

## Como usar:
1. Faça login no endpoint `/api/login` para obter o token JWT
2. Use o botão "Authorize" no topo desta página
3. Cole o token obtido (apenas o token, sem "Bearer")
4. Teste os endpoints protegidos

**Desenvolvido para:** Disciplina de Programação Web 2

**Equipe:** Eduardo Stopassole, João Machado, João Paulo de Oliveira Almeida, Roberto Paggi, Gustavo
        """,
        "version": "1.0.0",
        "contact": {
            "name": "Equipe de Desenvolvimento",
            "email": "suporte@estoque.com",
        },
    },
    "host": "localhost:5001",
    "basePath": "/api",
    "schemes": ["http"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Token JWT. Use o formato: Bearer SEU_TOKEN_AQUI",
        }
    },
    "tags": [
        {
            "name": "Autenticação",
            "description": "Endpoints de login e autenticação"
        },
        {
            "name": "Produtos",
            "description": "Operações CRUD de produtos"
        },
        {
            "name": "Estoque",
            "description": "Movimentações de entrada e saída de estoque"
        },
        {
            "name": "Categorias",
            "description": "Gestão de categorias de produtos (Requer Admin)"
        },
        {
            "name": "Locais",
            "description": "Gestão de locais de estoque (Requer Admin)"
        },
        {
            "name": "Fornecedores",
            "description": "Gestão de fornecedores (Requer Admin)"
        },
    ],
    "definitions": {
        "Usuario": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "nome_usuario": {"type": "string", "example": "admin"},
                "tipo_usuario": {
                    "type": "integer",
                    "example": 2,
                    "description": "1 = Operador, 2 = Administrador"
                },
            },
        },
        "Produto": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "nome_produto": {"type": "string", "example": "Caixa Isopor"},
                "custo_produto_Unit": {"type": "number", "format": "float", "example": 5.5},
                "valor_venda_Unit": {"type": "number", "format": "float", "example": 10.0},
                "id_local": {"type": "integer", "example": 1},
                "id_categoria": {"type": "integer", "example": 1},
                "id_fornecedor": {"type": "integer", "example": 1},
                "quantidade": {"type": "integer", "example": 100},
                "estoque_minimo": {"type": "integer", "example": 10},
            },
        },
        "ProdutoInput": {
            "type": "object",
            "required": [
                "nome_produto",
                "custo_produto_Unit",
                "valor_venda_Unit",
                "id_local",
                "id_categoria",
                "id_fornecedor"
            ],
            "properties": {
                "nome_produto": {"type": "string", "example": "Caixa Isopor"},
                "custo_produto_Unit": {"type": "number", "format": "float", "example": 5.5},
                "valor_venda_Unit": {"type": "number", "format": "float", "example": 10.0},
                "id_local": {"type": "integer", "example": 1},
                "id_categoria": {"type": "integer", "example": 1},
                "id_fornecedor": {"type": "integer", "example": 1},
                "quantidade": {"type": "integer", "example": 0, "default": 0},
                "estoque_minimo": {"type": "integer", "example": 0, "default": 0},
            },
        },
        "Categoria": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "nome_categoria": {"type": "string", "example": "Alimentos"},
            },
        },
        "LocalEstoque": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "nome_local": {"type": "string", "example": "Matriz"},
            },
        },
        "Fornecedor": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "nome_fornecedor": {"type": "string", "example": "Fornecedor X"},
            },
        },
        "LoginRequest": {
            "type": "object",
            "required": ["nome_usuario", "senha"],
            "properties": {
                "nome_usuario": {"type": "string", "example": "admin"},
                "senha": {"type": "string", "example": "123"},
            },
        },
        "LoginResponse": {
            "type": "object",
            "properties": {
                "access_token": {
                    "type": "string",
                    "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                },
            },
        },
        "MovimentacaoEstoque": {
            "type": "object",
            "required": ["quantidade"],
            "properties": {
                "quantidade": {
                    "type": "integer",
                    "example": 10,
                    "minimum": 1,
                    "description": "Quantidade a ser movimentada (deve ser maior que 0)"
                },
            },
        },
        "MovimentacaoResponse": {
            "type": "object",
            "properties": {
                "mensagem": {"type": "string", "example": "Entrada registrada"},
                "quantidade": {"type": "integer", "example": 10},
            },
        },
        "Erro": {
            "type": "object",
            "properties": {
                "erro": {"type": "string", "example": "Mensagem de erro"},
            },
        },
    },
}
