from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

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