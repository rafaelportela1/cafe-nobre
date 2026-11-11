from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafe_nobre.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(250))
    preco = db.Column(db.Float, nullable=False)
    estoque = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

print("Banco de dados do Café Nobre criado com sucesso!")