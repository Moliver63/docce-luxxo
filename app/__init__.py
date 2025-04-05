from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from werkzeug.utils import secure_filename
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa extensões
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configuração ESSENCIAL do Flask-Login
    login_manager.login_view = 'admin.login'  # Rota de login
    
    # Importação tardia para evitar circular imports
    with app.app_context():
        from app.models import Admin
    
        @login_manager.user_loader
        def load_user(user_id):
            return Admin.query.get(int(user_id))
    
        # Registra blueprints
        from app.routes import main, admin
        app.register_blueprint(main)
        app.register_blueprint(admin, url_prefix='/admin')

        # Cria tabelas
        db.create_all()
        
        # Cria admin padrão se não existir
        if not Admin.query.first():
            from werkzeug.security import generate_password_hash
            admin_user = Admin(
                username=app.config.get('ADMIN_USERNAME', 'admin'),
                password_hash=generate_password_hash(
                    app.config.get('ADMIN_PASSWORD', 'admin123')
                )
            )
            db.session.add(admin_user)
            db.session.commit()

    return app