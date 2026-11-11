from flask import (
    Flask, render_template_string, request,
    redirect, url_for, session, flash
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from zoneinfo import ZoneInfo
from datetime import timedelta
import json
import os
import secrets

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafe_nobre.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = (
    os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db = SQLAlchemy(app)

ADMIN_USUARIO = os.environ.get("CAFE_ADMIN_USUARIO", "admin")
ADMIN_SENHA = os.environ.get("CAFE_ADMIN_SENHA", "admin")
ADMIN_SENHA_HASH = generate_password_hash(ADMIN_SENHA)


# MODELOS DO BANCO

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(250), default="")
    preco = db.Column(db.Float, nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(30), nullable=False)
    total = db.Column(db.Float, nullable=False, default=0)

    # Horário de Brasília para os novos pedidos
    data_criacao = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("America/Sao_Paulo"))
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Recebido"
    )

    itens = db.relationship(
        "ItemPedido",
        backref="pedido",
        lazy=True,
        cascade="all, delete-orphan"
    )


class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(
        db.Integer, db.ForeignKey("pedido.id"), nullable=False
    )
    produto_id = db.Column(
        db.Integer, db.ForeignKey("produto.id"), nullable=False
    )
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    produto = db.relationship("Produto", lazy=True)


# PROTEÇÃO ADMINISTRATIVA

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logado"):
            return redirect(url_for("login_admin"))
        return func(*args, **kwargs)
    return wrapper


# VISUAL DA LOJA

ESTILO = """
<style> 

.banner-cafe {
    width: 100%;
    margin-top: 0;
    margin-bottom: 0;
    padding: 0;
    overflow: hidden;
      top: 0;      
}

.banner-cafe img {
    display: block;
    width: 100%;
    height: 420px;
    object-fit: cover;
  
}

@media (max-width: 768px) {
    .banner-cafe img {
        height: 230px;
    }
}


* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background:  #f8f3eb;
    color: #352719;
}
header {
    background: #4b2e20;
    color: white;
    margin-bottom: 0;
    padding-bottom: 0;
    padding: 22px 15px;
    text-align: center;
}
header h1 { margin: 0 0 8px; }
nav { margin-top: 14px; }
nav a {
    color: white;
    margin: 0 8px;
    text-decoration: none;
    font-weight: bold;
}
.container {
    max-width: 1100px;
    margin: 25px auto;
    padding: 0 15px;
}
.card {
    background: white;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 18px;
    box-shadow: 0 2px 8px #00000012;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 18px;
}
input, textarea {
    display: block;
    width: 100%;
    padding: 11px;
    margin: 8px 0 14px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 15px;
}
button, .botao {
    display: inline-block;
    background: #75472c;
    color: white;
    border: none;
    padding: 11px 15px;
    border-radius: 6px;
    cursor: pointer;
    text-decoration: none;
    margin: 3px 2px;
}
.excluir { background: #a52a2a; }
.preco {
    color: #347344;
    font-size: 21px;
    font-weight: bold;
}
.pequeno { color: #777; font-size: 13px; }
.linha {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
}
.mensagem {
    background: #fff0c9;
    padding: 12px;
    margin: 12px 0;
    border-radius: 6px;
}
table {
    width: 100%;
    border-collapse: collapse;
    background: white;
}
th, td {
    border-bottom: 1px solid #ddd;
    padding: 10px;
    text-align: left;
}
.rolagem { overflow-x: auto; }
footer {
    text-align: center;
    padding: 25px;
    color: #777;
}
@media (max-width: 600px) {
    nav a { display: inline-block; margin: 7px; }
    th, td { padding: 7px; font-size: 13px; }
}
.acesso-admin {
    display: block !important;
    text-align: center !important;
    padding: 18px !important;
    background-color: #352016 !important;
}

.acesso-admin a {
    color: #d6ad72 !important;
    font-size: 12px !important;
    font-weight: 400 !important;
    text-decoration: none !important;
    opacity: 0.85;
}

.acesso-admin a:hover {
    color: #ffffff !important;
    text-decoration: underline !important;
}
footer.rodape-cafe {
    display: block !important;
    width: 100% !important;
    box-sizing: border-box !important;
    background: #352016 !important;
    color: #eadcc8 !important;
    text-align: center !important;
    padding: 30px 15px !important;
    margin: 40px 0 0 0 !important;
}

.rodape-cafe .rodape-nome {
    color: #d6ad72 !important;
    font-size: 22px;
    font-weight: bold;
}

.rodape-cafe .rodape-frase {
    color: #eadcc8 !important;
}

.rodape-cafe .rodape-direitos {
    color: #cbbba6 !important;
}

.rodape-cafe .acesso-admin a {
    color: #D3AF37 !important;
    font-size: 12px;
    text-decoration: none;
}

.rodape-cafe .acesso-admin a:hover {
    color: #ffffff !important;
}
.icone-produto {
    width: 85px;
    height: 85px;
    object-fit: contain;
    display: block;
    margin: 0 auto 12px;

}


</style>
"""


def pagina_html(titulo, conteudo):
    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1.0">
            <title>{{ titulo }} - Café Nobre</title>
            """ + ESTILO + """
        </head>
        <body>
            <header>
  	    <nav>
        {% if session.get('admin_logado') %}
            <a href="{{ url_for('inicio') }}">Loja</a>
            <a href="{{ url_for('ver_estoque') }}">Estoque</a>
            <a href="{{ url_for('pedidos') }}">Pedidos</a>
            <a href="{{ url_for('admin_produtos') }}">Produtos</a>
   <form method="POST"
                              action="{{ url_for('logout_admin') }}"
                              style="display:inline">
                            <button type="submit">Sair</button>
                        </form>
                    {% else %}
<font face="Arial Black, sans-serif" size="4" color="#D3AF37">
                       <marquee behavior="efeito">Sejam Bem-Vindos ao Café Nobre - Qualidade e sabor em cada xicára</marquee>
                    {% endif %}
</font>
    </nav>
</header>

<section class="banner-cafe">
    <img
        src="{{ url_for('static', filename='banner-cafe-nobre.jpeg') }}"
        alt="Café Nobre - Qualidade e sabor em cada xícara">
</section>
            
            <main class="container">
                {% with mensagens = get_flashed_messages() %}
                    {% for mensagem in mensagens %}
                        <div class="mensagem">{{ mensagem }}</div>
                    {% endfor %}
                {% endwith %}
                {{ conteudo | safe }}
            </main>

          <footer class="rodape-cafe">
    <div class="rodape-nome">☕ Café Nobre</div>

    <div class="rodape-frase">
        Qualidade e sabor em cada xícara.
    </div>

    <div class="rodape-direitos">
        © {{ ano }} Café Nobre. Todos os direitos reservados.
    </div>

    <div class="acesso-admin">
        <a href="{{ url_for('login_admin') }}">
            Acesso administrativo
        </a>
    </div>
</footer>
        </body>
        </html>
        """,
        titulo=titulo,
        conteudo=conteudo,
        ano=datetime.now(ZoneInfo("America/Sao_Paulo")).year
    )


# LOJA INICIAL

@app.route("/")
def inicio():
    produtos = Produto.query.order_by(Produto.nome).all()

    conteudo = render_template_string(
        """

       <h2>Nossos produtos</h2>
<p>Escolha seus produtos e faça seu pedido.</p>

<div class="grid">
{% for produto in produtos %}
    <div class="card">

        {% if 'tradicional' in produto.nome|lower or 'classico' in produto.nome|lower or 'clássico' in produto.nome|lower %}
            <img src="{{ url_for('static', filename='icone-cafe-tradicional.jpeg') }}"
                 class="icone-produto" alt="Café Tradicional">

        {% elif 'especial' in produto.nome|lower %}
            <img src="{{ url_for('static', filename='icone-cafe-especial.jpeg') }}"
                 class="icone-produto" alt="Café Especial">

        {% elif 'premium' in produto.nome|lower %}
            <img src="{{ url_for('static', filename='icone-cafe-premium.jpeg') }}"
                 class="icone-produto" alt="Café Premium">
        {% endif %}

        <h3>{{ produto.nome }}</h3>

        <p>{{ produto.descricao or 'Produto Café Nobre' }}</p>

        <div class="preco">
            R$ {{ "%.2f"|format(produto.preco)|replace(".", ",") }}
        </div>

        {% if produto.estoque > 0 %}
            <button type="button"
                    onclick="adicionar({{ produto.id }})">
                Adicionar ao carrinho
            </button>
        {% else %}
            <p>Produto indisponível no momento.</p>
        {% endif %}

    </div>
{% else %}
    <div class="card">Nenhum produto cadastrado.</div>
{% endfor %}
</div>

        <section class="card">
            <h2>🛒 Meu carrinho</h2>
            <div id="carrinho">Seu carrinho está vazio.</div>
            <h3 id="total">Total: R$ 0,00</h3>
            <button type="button" onclick="limparCarrinho()">
                Limpar carrinho
            </button>

            <h3>Finalizar pedido</h3>
            <form method="POST"
                  action="{{ url_for('finalizar_pedido') }}"
                  onsubmit="return prepararPedido()">
                <label>Nome do cliente</label>
                <input type="text" name="cliente_nome"
                       maxlength="100" required>
                <label>Telefone</label>
                <input type="tel" name="telefone"
                       maxlength="30" required>
                <input type="hidden" name="itens_json" id="itens_json">
                <button type="submit">Confirmar pedido</button>
            </form>
        </section>

        <script>
        const produtos = {{ dados_produtos | tojson }};
        let carrinho = {};

        function moeda(valor) {
            return Number(valor).toLocaleString("pt-BR", {
                style: "currency", currency: "BRL"
            });
        }

        function adicionar(id) {
            const p = produtos[id];
            if (!p || p.estoque <= 0) return;
            if ((carrinho[id] || 0) >= p.estoque) {
                alert("Estoque insuficiente.");
                return;
            }
            carrinho[id] = (carrinho[id] || 0) + 1;
            atualizarCarrinho();
        }

        function alterarQuantidade(id, variacao) {
            if (!carrinho[id]) return;
            const nova = carrinho[id] + variacao;
            if (nova <= 0) delete carrinho[id];
            else if (nova <= produtos[id].estoque)
                carrinho[id] = nova;
            else alert("Estoque insuficiente.");
            atualizarCarrinho();
        }

        function limparCarrinho() {
            carrinho = {};
            atualizarCarrinho();
        }

        function atualizarCarrinho() {
            const area = document.getElementById("carrinho");
            const ids = Object.keys(carrinho);
            let total = 0;
            area.replaceChildren();

            if (!ids.length) {
                area.textContent = "Seu carrinho está vazio.";
            }

            ids.forEach(function(id) {
                const p = produtos[id];
                const qtd = carrinho[id];
                const subtotal = p.preco * qtd;
                total += subtotal;

                const linha = document.createElement("div");
                linha.className = "linha";

                const texto = document.createElement("span");
                texto.textContent = p.nome + " — " + qtd +
                    " x " + moeda(p.preco) + " = " + moeda(subtotal);

                const controles = document.createElement("span");
                const menos = document.createElement("button");
                menos.type = "button";
                menos.textContent = "−";
                menos.onclick = () => alterarQuantidade(id, -1);

                const mais = document.createElement("button");
                mais.type = "button";
                mais.textContent = "+";
                mais.onclick = () => alterarQuantidade(id, 1);

                controles.append(menos, mais);
                linha.append(texto, controles);
                area.appendChild(linha);
            });

            document.getElementById("total").textContent =
                "Total: " + moeda(total);
        }

        function prepararPedido() {
            if (!Object.keys(carrinho).length) {
                alert("Adicione pelo menos um produto.");
                return false;
            }

            document.getElementById("itens_json").value =
                JSON.stringify(Object.entries(carrinho).map(
                    item => ({
                        produto_id: Number(item[0]),
                        quantidade: item[1]
                    })
                ));
            return true;
        }
        </script>
        """,
        produtos=produtos,
        dados_produtos={
            str(p.id): {
                "nome": p.nome,
                "preco": p.preco,
                "estoque": p.estoque
            } for p in produtos
        }
    )

    return pagina_html("Início", conteudo)


# FINALIZAR PEDIDO

@app.route("/finalizar-pedido", methods=["POST"])
def finalizar_pedido():
    nome = request.form.get("cliente_nome", "").strip()
    telefone = request.form.get("telefone", "").strip()

    try:
        itens = json.loads(request.form.get("itens_json", ""))
        if not isinstance(itens, list) or not itens:
            raise ValueError
        if not nome or not telefone or len(nome) > 100 or len(telefone) > 30:
            raise ValueError
    except (ValueError, TypeError, json.JSONDecodeError):
        flash("Confira os dados e os produtos do pedido.")
        return redirect(url_for("inicio"))

    quantidades = {}

    try:
        for item in itens:
            pid = int(item["produto_id"])
            qtd = int(item["quantidade"])
            if pid <= 0 or qtd <= 0:
                raise ValueError
            quantidades[pid] = quantidades.get(pid, 0) + qtd
    except (ValueError, TypeError, KeyError):
        flash("Itens do pedido inválidos.")
        return redirect(url_for("inicio"))

    try:
        linhas = []
        total = 0

        for pid, qtd in quantidades.items():
            produto = db.session.get(Produto, pid)
            if produto is None:
                raise ValueError("Produto não encontrado.")
            if qtd > produto.estoque:
                raise ValueError("Estoque insuficiente para " + produto.nome)

            subtotal = round(produto.preco * qtd, 2)
            total += subtotal
            linhas.append((produto, qtd, produto.preco, subtotal))

        pedido = Pedido(
            cliente_nome=nome,
            telefone=telefone,
            total=round(total, 2),
            status="Recebido"
        )
        db.session.add(pedido)
        db.session.flush()

        for produto, qtd, preco, subtotal in linhas:
            produto.estoque -= qtd
            db.session.add(ItemPedido(
                pedido_id=pedido.id,
                produto_id=produto.id,
                quantidade=qtd,
                preco_unitario=preco,
                subtotal=subtotal
            ))

        db.session.commit()

    except ValueError as erro:
        db.session.rollback()
        flash(str(erro))
        return redirect(url_for("inicio"))
    except Exception:
        db.session.rollback()
        app.logger.exception("Erro ao salvar pedido")
        flash("Não foi possível salvar o pedido.")
        return redirect(url_for("inicio"))

    conteudo = render_template_string(
        """
        <div class="card">
            <h2>Pedido realizado com sucesso!</h2>
            <p>Obrigado, {{ pedido.cliente_nome }}.</p>
            <p>Número do pedido: {{ pedido.id }}</p>
            <p>
                Total: R$ {{ "%.2f"|format(pedido.total)|replace(".", ",") }}
            </p>
            <p>Status: {{ pedido.status }}</p>
            <a class="botao" href="{{ url_for('inicio') }}">
                Voltar à loja
            </a>
        </div>
        """,
        pedido=pedido
    )
    return pagina_html("Pedido confirmado", conteudo)

# LOGIN ADMINISTRATIVO

@app.route("/admin/login", methods=["GET", "POST"])
def login_admin():
    if session.get("admin_logado"):
        return redirect(url_for("admin_produtos"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        senha = request.form.get("senha", "")

        if (
            secrets.compare_digest(usuario, ADMIN_USUARIO)
            and check_password_hash(ADMIN_SENHA_HASH, senha)
        ):
            session.clear()
            session["admin_logado"] = True
            session["admin_usuario"] = ADMIN_USUARIO
            return redirect(url_for("admin_produtos"))

        flash("Usuário ou senha incorretos.")

    conteudo = """
    <div class="card" style="max-width:450px;margin:auto">
        <h2>Área administrativa</h2>
        <form method="POST">
            <label>Usuário</label>
            <input type="text" name="usuario"
                   autocomplete="username" required>
            <label>Senha</label>
            <input type="password" name="senha"
                   autocomplete="current-password" required>
            <button type="submit">Entrar</button>
        </form>
    </div>
    """
    return pagina_html("Login", conteudo)


@app.route("/admin/logout", methods=["POST"])
@admin_required
def logout_admin():
    session.clear()
    flash("Você saiu da área administrativa.")
    return redirect(url_for("login_admin"))


# CONSULTA DE ESTOQUE

@app.route("/ver-estoque")
@admin_required
def ver_estoque():
    produtos = Produto.query.order_by(Produto.nome).all()

    conteudo = render_template_string(
        """
        <h2>Controle de estoque</h2>
        <div class="card rolagem">
            <table>
                <thead>
                    <tr>
                        <th>Produto</th>
                        <th>Preço</th>
                        <th>Estoque</th>
                    </tr>
                </thead>
                <tbody>
                    {% for produto in produtos %}
                    <tr>
                        <td>{{ produto.nome }}</td>
                        <td>
                            R$ {{ "%.2f"|format(produto.preco)|replace(".", ",") }}
                        </td>
                        <td>{{ produto.estoque }}</td>
                    </tr>
                    {% else %}
                    <tr><td colspan="3">Nenhum produto cadastrado.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        """,
        produtos=produtos
    )
    return pagina_html("Estoque", conteudo)


# CONSULTA DE PEDIDOS

@app.route("/pedidos")
@admin_required
def pedidos():
    lista = Pedido.query.order_by(
        Pedido.data_criacao.desc(), Pedido.id.desc()
    ).all()

    conteudo = render_template_string(
        """
        <h2>Pedidos realizados</h2>

        {% for pedido in pedidos %}
        <div class="card">
            <h3>Pedido #{{ pedido.id }}</h3>

            <p><strong>Cliente:</strong> {{ pedido.cliente_nome }}</p>
            <p><strong>Telefone:</strong> {{ pedido.telefone }}</p>

            <p><strong>Data:</strong>
            {{ pedido.data_criacao.strftime("%d/%m/%Y %H:%M") if pedido.data_criacao else "-" }}
            </p>

            <p><strong>Status:</strong> {{ pedido.status }}</p>

            <h4>Itens</h4>
            <ul>
                {% for item in pedido.itens %}
                <li>
                    {{ item.produto.nome }} — {{ item.quantidade }} unidade(s)
                    — R$ {{ "%.2f"|format(item.subtotal)|replace(".", ",") }}
                </li>
                {% endfor %}
            </ul>

            <h3>
                Total: R$ {{ "%.2f"|format(pedido.total)|replace(".", ",") }}
            </h3>

            <form method="POST"
                  action="{{ url_for('excluir_pedido', pedido_id=pedido.id) }}"
                  onsubmit="return confirm('Tem certeza que deseja excluir este pedido?');">

                <button type="submit"
                        style="background:#b52b2b; color:white; border:none;
                        padding:10px 18px; border-radius:6px; cursor:pointer;">
                    Excluir pedido
                </button>
            </form>
        </div>

        {% else %}
        <div class="card">Nenhum pedido registrado.</div>
        {% endfor %}
        """,
        pedidos=lista
    )

    return pagina_html("Pedidos", conteudo)

# EXCLUIR PEDIDO

@app.route("/excluir-pedido/<int:pedido_id>", methods=["POST"])
@admin_required
def excluir_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)

    try:
        for item in pedido.itens:
            db.session.delete(item)

        db.session.delete(pedido)
        db.session.commit()

        return redirect(url_for("pedidos"))

    except Exception:
        db.session.rollback()
        raise

# CADASTRAR E LISTAR PRODUTOS

@app.route("/admin/produtos", methods=["GET", "POST"])
@admin_required
def admin_produtos():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()

        try:
            preco = float(request.form.get("preco", ""))
            estoque = int(request.form.get("estoque", ""))
        except (ValueError, TypeError):
            flash("Informe preço e estoque válidos.")
            return redirect(url_for("admin_produtos"))

        if not nome or len(nome) > 100 or len(descricao) > 250:
            flash("Confira o nome e a descrição.")
            return redirect(url_for("admin_produtos"))

        if preco < 0 or estoque < 0:
            flash("Preço e estoque não podem ser negativos.")
            return redirect(url_for("admin_produtos"))

        db.session.add(Produto(
            nome=nome,
            descricao=descricao,
            preco=preco,
            estoque=estoque
        ))
        db.session.commit()
        flash("Produto cadastrado com sucesso.")
        return redirect(url_for("admin_produtos"))

    produtos = Produto.query.order_by(Produto.nome).all()

    conteudo = render_template_string(
        """
        <h2>Gerenciar produtos</h2>
        <div class="card">
            <h3>Cadastrar novo produto</h3>
            <form method="POST">
                <label>Nome</label>
                <input name="nome" maxlength="100" required>
                <label>Descrição</label>
                <textarea name="descricao" maxlength="250"></textarea>
                <label>Preço (R$)</label>
                <input type="number" name="preco"
                       min="0" step="0.01" required>
                <label>Estoque</label>
                <input type="number" name="estoque"
                       min="0" step="1" required>
                <button type="submit">Cadastrar produto</button>
            </form>
        </div>

        {% for produto in produtos %}
        <div class="card">
            <h3>{{ produto.nome }}</h3>
            <p>{{ produto.descricao }}</p>
            <p>Preço: R$ {{ "%.2f"|format(produto.preco)|replace(".", ",") }}</p>
            <p>Estoque: {{ produto.estoque }}</p>
            <a class="botao"
               href="{{ url_for('editar_produto', produto_id=produto.id) }}">
                Editar
            </a>
            <form method="POST"
                  action="{{ url_for('excluir_produto', produto_id=produto.id) }}"
                  onsubmit="return confirm('Deseja excluir este produto?')"
                  style="display:inline">
                <button class="excluir" type="submit">Excluir</button>
            </form>
        </div>
        {% else %}
        <div class="card">Nenhum produto cadastrado.</div>
        {% endfor %}
        """,
        produtos=produtos
    )
    return pagina_html("Produtos", conteudo)


# EDITAR PRODUTOS

@app.route("/admin/produtos/editar/<int:produto_id>", methods=["GET", "POST"])
@admin_required
def editar_produto(produto_id):
    produto = db.session.get(Produto, produto_id)

    if produto is None:
        flash("Produto não encontrado.")
        return redirect(url_for("admin_produtos"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()

        try:
            preco = float(request.form.get("preco", ""))
            estoque = int(request.form.get("estoque", ""))
        except (ValueError, TypeError):
            flash("Informe preço e estoque válidos.")
            return redirect(url_for("editar_produto", produto_id=produto.id))

        if (
            not nome or len(nome) > 100 or len(descricao) > 250
            or preco < 0 or estoque < 0
        ):
            flash("Confira os dados do produto.")
            return redirect(url_for("editar_produto", produto_id=produto.id))

        produto.nome = nome
        produto.descricao = descricao
        produto.preco = preco
        produto.estoque = estoque
        db.session.commit()

        flash("Produto atualizado com sucesso.")
        return redirect(url_for("admin_produtos"))

    conteudo = render_template_string(
        """
        <div class="card">
            <h2>Editar produto</h2>
            <form method="POST">
                <label>Nome</label>
                <input name="nome" maxlength="100"
                       value="{{ produto.nome }}" required>
                <label>Descrição</label>
                <textarea name="descricao" maxlength="250">{{ produto.descricao or "" }}</textarea>
                <label>Preço</label>
                <input type="number" name="preco" min="0" step="0.01"
                       value="{{ produto.preco }}" required>
                <label>Estoque</label>
                <input type="number" name="estoque" min="0" step="1"
                       value="{{ produto.estoque }}" required>
                <button type="submit">Salvar alterações</button>
                <a class="botao" href="{{ url_for('admin_produtos') }}">
                    Cancelar
                </a>
            </form>
        </div>
        """,
        produto=produto
    )
    return pagina_html("Editar produto", conteudo)


# EXCLUIR PRODUTOS

@app.route("/admin/produtos/excluir/<int:produto_id>", methods=["POST"])
@admin_required
def excluir_produto(produto_id):
    produto = db.session.get(Produto, produto_id)

    if produto is None:
        flash("Produto não encontrado.")
        return redirect(url_for("admin_produtos"))

    possui_pedidos = ItemPedido.query.filter_by(
        produto_id=produto.id
    ).first()

    if possui_pedidos:
        flash("Este produto tem histórico de pedidos e não pode ser excluído.")
        return redirect(url_for("admin_produtos"))

    db.session.delete(produto)
    db.session.commit()
    flash("Produto excluído com sucesso.")
    return redirect(url_for("admin_produtos"))


# INICIALIZAÇÃO DO BANCO

def inicializar_banco():
    with app.app_context():
        db.create_all()

        if Produto.query.count() == 0:
            db.session.add_all([
                Produto(
                    nome="Café Tradicional",
                    descricao="Café para o dia a dia.",
                    preco=15.90,
                    estoque=30
                ),
                Produto(
                    nome="Café Gourmet",
                    descricao="Café selecionado de qualidade superior.",
                    preco=24.90,
                    estoque=20
                ),
                Produto(
                    nome="Café Especial",
                    descricao="Aroma marcante e sabor diferenciado.",
                    preco=32.90,
                    estoque=15
                ),
                Produto(
                    nome="Cappuccino",
                    descricao="Mistura cremosa para preparar sua bebida.",
                    preco=18.90,
                    estoque=25
                )
            ])
            db.session.commit()


if __name__ == "__main__":
    inicializar_banco()
    app.run(debug=True)

# --------------------------------------------------
# CONSULTA DE ESTOQUE
# --------------------------------------------------


@app.route("/ver-estoque")
@admin_required
def ver_estoque_admin():
    produtos = Produto.query.order_by(Produto.nome).all()

    conteudo = render_template_string(
        """
        <h2>Controle de estoque</h2>

        <div class="card rolagem">
            <table>
                <thead>
                    <tr>
                        <th>Produto</th>
                        <th>Preço</th>
                        <th>Estoque</th>
                    </tr>
                </thead>
                <tbody>
                    {% for produto in produtos %}
                    <tr>
                        <td>{{ produto.nome }}</td>
                        <td>
                            R$ {{ "%.2f"|format(produto.preco)|replace(".", ",") }}
                        </td>
                        <td>{{ produto.estoque }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="3">Nenhum produto cadastrado.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        """,
        produtos=produtos,
    )

    return pagina_html("Estoque", conteudo)


# --------------------------------------------------
# CONSULTA DE PEDIDOS
# --------------------------------------------------

@app.route("/pedidos")
@admin_required
def meus_pedidos():
    lista_pedidos = Pedido.query.order_by(
        Pedido.data_criacao.desc(),
        Pedido.id.desc(),
    ).all()

    conteudo = render_template_string(
        """
        <h2>Pedidos realizados</h2>

        {% for pedido in pedidos %}
        <div class="card">
            <h3>Pedido #{{ pedido.id }}</h3>

            <p><strong>Cliente:</strong> {{ pedido.cliente_nome }}</p>
            <p><strong>Telefone:</strong> {{ pedido.telefone }}</p>
            <p>
f                <strong>Data:</strong>
                {{ pedido.data_criacao.strftime("%d/%m/%Y %H:%M")
                   if pedido.data_criacao else "-" }}
            </p>
            <p><strong>Status:</strong> {{ pedido.status }}</p>

            <h4>Itens</h4>

            <ul>
                {% for item in pedido.itens %}
                <li>
                    {{ item.produto.nome }} —
                    {{ item.quantidade }} unidade(s) —
                    R$ {{ "%.2f"|format(item.subtotal)|replace(".", ",") }}
                </li>
                {% endfor %}
            </ul>

            <h3>
                Total:
                R$ {{ "%.2f"|format(pedido.total)|replace(".", ",") }}
            </h3>
        </div>
        {% else %}
        <div class="card">Nenhum pedido registrado.</div>
        {% endfor %}
        """,
        pedidos=lista_pedidos,
    )

    return pagina_html("Pedidos", conteudo)


# --------------------------------------------------
# CADASTRO E LISTAGEM DE PRODUTOS
# --------------------------------------------------

@app.route("/admin/produtos", methods=["GET", "POST"])
def gerenciar_produtos_admin():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()

        try:
            preco = float(request.form.get("preco", ""))
            estoque = int(request.form.get("estoque", ""))
        except (ValueError, TypeError):
            flash("Informe um preço e uma quantidade válidos.")
            return redirect(url_for("admin_produtos"))

        if not nome or len(nome) > 100:
            flash("Informe um nome válido para o produto.")
            return redirect(url_for("admin_produtos"))

        if len(descricao) > 250:
            flash("A descrição deve ter até 250 caracteres.")
            return redirect(url_for("admin_produtos"))

        if preco < 0 or estoque < 0:
            flash("Preço e estoque não podem ser negativos.")
            return redirect(url_for("admin_produtos"))

        produto = Produto(
            nome=nome,
            descricao=descricao,
            preco=preco,
            estoque=estoque,
        )

        db.session.add(produto)
        db.session.commit()

        flash("Produto cadastrado com sucesso.")
        return redirect(url_for("admin_produtos"))

    produtos = Produto.query.order_by(Produto.nome).all()

    conteudo = render_template_string(
        """
        <h2>Gerenciar produtos</h2>

        <div class="card">
            <h3>Cadastrar novo produto</h3>

            <form method="POST">
                <label>Nome do produto</label>
                <input type="text" name="nome" maxlength="100" required>

                <label>Descrição</label>
                <textarea name="descricao" maxlength="250"></textarea>

                <label>Preço (R$)</label>
                <input type="number" name="preco"
                       min="0" step="0.01" required>

                <label>Quantidade em estoque</label>
                <input type="number" name="estoque"
                       min="0" step="1" required>

                <button type="submit">Cadastrar produto</button>
            </form>
        </div>

        <h3>Produtos cadastrados</h3>

        {% for produto in produtos %}
        <div class="card">
            <div class="linha">
                <div>
                    <h3>{{ produto.nome }}</h3>
                    <p>{{ produto.descricao }}</p>
                    <p>
                        Preço:
                        R$ {{ "%.2f"|format(produto.preco)|replace(".", ",") }}
                    </p>
                    <p>Estoque: {{ produto.estoque }}</p>
                </div>

                <div>
                    <a class="botao"
                       href="{{ url_for('editar_produto',
                                        produto_id=produto.id) }}">
                        Editar
                    </a>

                    <form method="POST"
                          action="{{ url_for('excluir_produto',
                                             produto_id=produto.id) }}"
                          onsubmit="return confirm('Deseja excluir este produto?')"
                          style="display:inline">
                        <button class="excluir" type="submit">
                            Excluir
                        </button>
                    </form>
                </div>
            </div>
        </div>
        {% else %}
        <div class="card">Nenhum produto cadastrado.</div>
        {% endfor %}
        """,
        produtos=produtos,
    )

    return pagina_html("Gerenciar produtos", conteudo)


# --------------------------------------------------
# EDIÇÃO DE PRODUTOS
# --------------------------------------------------

@app.route(
    "/admin/produtos/editar/<int:produto_id>",
    methods=["GET", "POST"],
)
@admin_required
def editar_produto(produto_id):
    produto = db.session.get(Produto, produto_id)

    if produto is None:
        flash("Produto não encontrado.")
        return redirect(url_for("admin_produtos"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()

        try:
            preco = float(request.form.get("preco", ""))
            estoque = int(request.form.get("estoque", ""))
        except (ValueError, TypeError):
            flash("Informe um preço e uma quantidade válidos.")
            return redirect(
                url_for("editar_produto", produto_id=produto.id)
            )

        if not nome or len(nome) > 100:
            flash("Informe um nome válido para o produto.")
            return redirect(
                url_for("editar_produto", produto_id=produto.id)
            )

        if len(descricao) > 250:
            flash("A descrição deve ter até 250 caracteres.")
            return redirect(
                url_for("editar_produto", produto_id=produto.id)
            )

        if preco < 0 or estoque < 0:
            flash("Preço e estoque não podem ser negativos.")
            return redirect(
                url_for("editar_produto", produto_id=produto.id)
            )

        produto.nome = nome
        produto.descricao = descricao
        produto.preco = preco
        produto.estoque = estoque

        db.session.commit()

        flash("Produto atualizado com sucesso.")
        return redirect(url_for("admin_produtos"))

    conteudo = render_template_string(
        """
        <div class="card">
            <h2>Editar produto</h2>

            <form method="POST">
                <label>Nome</label>
                <input type="text" name="nome" maxlength="100"
                       value="{{ produto.nome }}" required>

                <label>Descrição</label>
                <textarea name="descricao"
                          maxlength="250">{{ produto.descricao or "" }}</textarea>

                <label>Preço (R$)</label>
                <input type="number" name="preco" min="0" step="0.01"
                       value="{{ produto.preco }}" required>

                <label>Estoque</label>
                <input type="number" name="estoque" min="0" step="1"
                       value="{{ produto.estoque }}" required>

                <button type="submit">Salvar alterações</button>

                <a class="botao" href="{{ url_for('admin_produtos') }}">
                    Cancelar
                </a>
            </form>
        </div>
        """,
        produto=produto,
    )

    return pagina_html("Editar produto", conteudo)


# --------------------------------------------------
# EXCLUSÃO DE PRODUTOS
# --------------------------------------------------

@app.route(
    "/admin/produtos/excluir/<int:produto_id>",
    methods=["POST"],
)
@admin_required
def excluir_produto(produto_id):
    produto = db.session.get(Produto, produto_id)

    if produto is None:
        flash("Produto não encontrado.")
        return redirect(url_for("admin_produtos"))

    possui_pedidos = ItemPedido.query.filter_by(
        produto_id=produto.id
    ).first()

    if possui_pedidos:
        flash(
            "Este produto já possui histórico de pedidos "
            "e não pode ser excluído."
        )
        return redirect(url_for("admin_produtos"))

    db.session.delete(produto)
    db.session.commit()

    flash("Produto excluído com sucesso.")
    return redirect(url_for("admin_produtos"))


# --------------------------------------------------
# CRIAÇÃO DO BANCO E PRODUTOS INICIAIS
# --------------------------------------------------

def inicializar_banco():
    with app.app_context():
        db.create_all()

        if Produto.query.count() == 0:
            produtos_iniciais = [
                Produto(
                    nome="Café Tradicional",
                    descricao="Café para o dia a dia.",
                    preco=15.90,
                    estoque=30,
                ),
                Produto(
                    nome="Café Gourmet",
                    descricao="Café selecionado de qualidade superior.",
                    preco=24.90,
                    estoque=20,
                ),
                Produto(
                    nome="Café Especial",
                    descricao="Aroma marcante e sabor diferenciado.",
                    preco=32.90,
                    estoque=15,
                ),
                Produto(
                    nome="Cappuccino",
                    descricao="Mistura cremosa para preparar sua bebida.",
                    preco=18.90,
                    estoque=25,
                ),
            ]

            db.session.add_all(produtos_iniciais)
            db.session.commit()


# --------------------------------------------------
# EXECUÇÃO DA APLICAÇÃO
# --------------------------------------------------
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
