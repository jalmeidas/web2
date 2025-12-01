API de Estoque – Documentação
Visão geral
Esta API expõe os mesmos recursos do sistema web de estoque (produtos, categorias, locais, fornecedores) para integração com o aplicativo mobile. A autenticação é feita via token JWT enviado no cabeçalho Authorization: Bearer <token> em todas as rotas protegidas.

Autenticação
Login
Endpoint: POST /api/login

Descrição: Gera um token JWT para o usuário.

Corpo (JSON):

json
{
  "nome_usuario": "admin",
  "senha": "123"
}
Resposta 200 (OK):

json
{
  "access_token": "JWT_AQUI"
}
Erros comuns:

400 – Campos obrigatórios ausentes.

401 – Usuário não encontrado ou senha inválida.

O payload do token inclui, por exemplo:

json
{
  "id": 1,
  "nome_usuario": "admin",
  "tipo_usuario": 2
}
Cabeçalhos obrigatórios
Para todas as rotas protegidas:

text
Authorization: Bearer SEU_TOKEN_JWT
Content-Type: application/json
Regras de acesso por perfil
Operador (tipo_usuario = 1):

Pode listar produtos, categorias, locais e fornecedores.

Pode registrar entrada e saída de estoque de produtos.

Administrador (tipo_usuario = 2):

Tudo que o operador faz.

Pode criar, atualizar e excluir produtos.

Pode criar e excluir categorias, locais e fornecedores.

Se o perfil não tiver permissão, a API retorna 403 – Acesso restrito a administradores.

Produtos
Listar produtos
Endpoint: GET /api/produtos

Autenticação: JWT obrigatório.

Descrição: Retorna lista de todos os produtos.

Resposta 200 (OK) – Exemplo:

json
[
  {
    "id": 1,
    "nome_produto": "Caixa Isopor",
    "custo_produto_Unit": 5.5,
    "valor_venda_Unit": 10.0,
    "id_local": 1,
    "id_categoria": 1,
    "id_fornecedor": 1,
    "quantidade": 55,
    "estoque_minimo": 5
  }
]
Criar produto
Endpoint: POST /api/produtos

Autenticação: JWT obrigatório (recomendado admin).

Descrição: Cria um novo produto.

Corpo (JSON):

json
{
  "nome_produto": "Caixa Isopor",
  "custo_produto_Unit": 5.5,
  "valor_venda_Unit": 10.0,
  "id_local": 1,
  "id_categoria": 1,
  "id_fornecedor": 1,
  "quantidade": 10,
  "estoque_minimo": 2
}
Resposta 201 (Created):

json
{
  "id": 1,
  "nome_produto": "Caixa Isopor",
  "custo_produto_Unit": 5.5,
  "valor_venda_Unit": 10.0,
  "id_local": 1,
  "id_categoria": 1,
  "id_fornecedor": 1,
  "quantidade": 10,
  "estoque_minimo": 2
}
Erros:

400 – Campos obrigatórios faltando.

Obter produto por ID
Endpoint: GET /api/produtos/{id}

Autenticação: JWT obrigatório.

Descrição: Retorna um produto específico.

Resposta 200 (OK):

json
{
  "id": 1,
  "nome_produto": "Caixa Isopor",
  "custo_produto_Unit": 5.5,
  "valor_venda_Unit": 10.0,
  "id_local": 1,
  "id_categoria": 1,
  "id_fornecedor": 1,
  "quantidade": 10,
  "estoque_minimo": 2
}
Erros:

404 – Produto não encontrado.

Atualizar produto
Endpoint: PUT /api/produtos/{id}

Autenticação: JWT obrigatório (admin).

Descrição: Atualiza campos de um produto.

Corpo (JSON) – exemplo:

json
{
  "nome_produto": "Caixa Isopor Grande",
  "quantidade": 20,
  "estoque_minimo": 5
}
Resposta 200 (OK): produto atualizado.

Erros:

400 – Nada para atualizar.

404 – Produto não encontrado.

Deletar produto
Endpoint: DELETE /api/produtos/{id}

Autenticação: JWT obrigatório (admin).

Descrição: Remove um produto.

Resposta 204 (No Content): sem corpo.

Erros:

404 – Produto não encontrado.

400 – Erro de regra de negócio ou integridade.

Regra de negócio: Estoque
Registrar entrada de estoque
Endpoint: POST /api/produtos/{id}/entrada

Autenticação: JWT obrigatório (operador ou admin).

Descrição: Aumenta a quantidade em estoque de um produto.

Corpo (JSON):

json
{
  "quantidade": 5
}
Resposta 200 (OK):

json
{
  "mensagem": "Entrada registrada",
  "quantidade": 5
}
Erros:

400 – Quantidade inválida (> 0 obrigatório) ou produto não encontrado.

Registrar saída de estoque
Endpoint: POST /api/produtos/{id}/saida

Autenticação: JWT obrigatório (operador ou admin).

Descrição: Reduz a quantidade em estoque, respeitando estoque atual e mínimo.

Corpo (JSON):

json
{
  "quantidade": 3
}
Resposta 200 (OK):

json
{
  "mensagem": "Saída registrada",
  "quantidade": 3
}
Regras aplicadas:

Não permite saída maior que o estoque disponível.

Se o saldo ficar abaixo de estoque_minimo, o sistema sinaliza essa situação.

Erros:

400 – Estoque insuficiente, quantidade inválida ou produto não encontrado.

Categorias
Listar categorias
Endpoint: GET /api/categorias

Autenticação: JWT obrigatório.

Resposta 200 (OK):

json
[
  {
    "id": 1,
    "nome_categoria": "Alimentos"
  }
]
Criar categoria
Endpoint: POST /api/categorias

Autenticação: JWT obrigatório (admin).

Corpo (JSON):

json
{
  "nome_categoria": "Alimentos"
}
Resposta 201 (Created):

json
{
  "id": 1,
  "nome_categoria": "Alimentos"
}
Erros:

400 – nome_categoria ausente.

403 – Usuário não é administrador.

Deletar categoria
Endpoint: DELETE /api/categorias/{id}

Autenticação: JWT obrigatório (admin).

Resposta 204 (No Content).

Erros:

404 – Categoria não encontrada.

400 – Existem produtos usando esta categoria.

Locais de estoque
Listar locais
Endpoint: GET /api/locais

Autenticação: JWT obrigatório.

Resposta 200 (OK):

json
[
  {
    "id": 1,
    "nome_local": "Matriz"
  }
]
Criar local
Endpoint: POST /api/locais

Autenticação: JWT obrigatório (admin).

Corpo (JSON):

json
{
  "nome_local": "Matriz"
}
Resposta 201 (Created).

Deletar local
Endpoint: DELETE /api/locais/{id}

Autenticação: JWT obrigatório (admin).

Resposta 204 (No Content).

Erros:

404 – Local não encontrado.

400 – Existem produtos cadastrados neste local.

Fornecedores
Listar fornecedores
Endpoint: GET /api/fornecedores

Autenticação: JWT obrigatório.

Resposta 200 (OK):

json
[
  {
    "id": 1,
    "nome_fornecedor": "Fornecedor X"
  }
]
Criar fornecedor
Endpoint: POST /api/fornecedores

Autenticação: JWT obrigatório (admin).

Corpo (JSON):

json
{
  "nome_fornecedor": "Fornecedor X"
}
Resposta 201 (Created).

Deletar fornecedor
Endpoint: DELETE /api/fornecedores/{id}

Autenticação: JWT obrigatório (admin).

Resposta 204 (No Content).

Erros:

404 – Fornecedor não encontrado.

400 – Existem produtos vinculados a este fornecedor.

Códigos de status
200 OK – Operação realizada com sucesso.

201 Created – Recurso criado com sucesso.

204 No Content – Recurso deletado com sucesso, sem corpo.

400 Bad Request – Erro de validação ou regra de negócio.

401 Unauthorized – Token ausente ou inválido.

403 Forbidden – Usuário autenticado sem permissão (não é admin).

404 Not Found – Recurso não encontrado.