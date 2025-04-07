from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Joia(db.Model):
    """
    Modelo para representar joias no banco de dados.
    """
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        """
        Converte o objeto Joia em um dicionário para uso em APIs ou templates.
        """
        return {
            "id": self.id,
            "nome": self.nome,
            "preco": self.preco,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "foto": self.foto
        }

    def __repr__(self):
        """
        Representação legível do objeto Joia.
        """
        return f"<Joia {self.nome}>"

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """
        Representação legível do objeto Admin.
        """
        return f"<Admin {self.username}>"

# Nova tabela para Pedidos
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.String(50), unique=True, nullable=False)
    data_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pendente')
    valor_total = db.Column(db.Float, nullable=False)
    # Relacionamento com Joia (um pedido pode ter várias joias)
    joias = db.relationship('JoiaPedido', backref='pedido', lazy=True)
    # Relacionamento com Pagamento
    pagamento_id = db.Column(db.Integer, db.ForeignKey('pagamento.id'))

# Nova tabela para associar Joias a Pedidos (caso um pedido tenha várias joias)
class JoiaPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    joia_id = db.Column(db.Integer, db.ForeignKey('joia.id'), nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=1)

# Nova tabela para Pagamentos
class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_pagamento = db.Column(db.String(50), nullable=False)  # PIX, Cartão, etc.
    status_pagamento = db.Column(db.String(50), default='pendente')
    valor = db.Column(db.Float, nullable=False)
    data_pagamento = db.Column(db.DateTime)
    external_reference = db.Column(db.String(100))  # Referência externa (ex: Asaas)
    qr_code = db.Column(db.String(500))  # QR Code para PIX
    screenshot_pagamento = db.Column(db.String(200))  # Captura de tela do pagamento (opcional)
    # Relacionamento com Conversão de Moeda
    conversao_id = db.Column(db.Integer, db.ForeignKey('conversao_moeda.id'))

# Nova tabela para Conversão de Moeda (BRL para USDT)
class ConversaoMoeda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor_brl = db.Column(db.Float, nullable=False)
    valor_usdt = db.Column(db.Float, nullable=False)
    taxa_conversao = db.Column(db.Float, nullable=False)
    data_conversao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pendente')
    # Relacionamento com Pagamento
    pagamento = db.relationship('Pagamento', backref='conversao', uselist=False)