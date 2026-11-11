from criar_banco import app, db, Produto

with app.app_context():
    cafes = [
        Produto(
            nome="Café Clássico",
            descricao="Café tradicional para o dia a dia",
            preco=24.90,
            estoque=20
        ),
        Produto(
            nome="Café Especial",
            descricao="Café especial de sabor marcante",
            preco=34.90,
            estoque=15
        ),
        Produto(
            nome="Café Premium",
            descricao="Café premium selecionado",
            preco=44.90,
            estoque=10
        )
    ]

    for cafe in cafes:
        existente = Produto.query.filter_by(nome=cafe.nome).first()
        if existente is None:
            db.session.add(cafe)

    db.session.commit()

    print("\nProdutos cadastrados no banco:\n")
    for produto in Produto.query.all():
        print(produto.nome, "- R$", produto.preco, "- Estoque:", produto.estoque)