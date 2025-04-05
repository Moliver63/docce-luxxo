import os
from uuid import uuid4

class Config:
    # Configurações de Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-complexa-aqui-123'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuração do Banco de Dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///joias.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Configurações de Upload
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_FOLDER = os.path.join(BASE_DIR, 'app', 'static')
    
    # Pastas de Upload
    UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')
    THUMBNAIL_FOLDER = os.path.join(UPLOAD_FOLDER, 'thumbnails')
    PROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, 'processed')
    
    # Criar pastas se não existirem
    for folder in [UPLOAD_FOLDER, THUMBNAIL_FOLDER, PROCESSED_FOLDER]:
        os.makedirs(folder, exist_ok=True)

    # Tipos de Arquivo Permitidos
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    ALLOWED_MIMETYPES = {
        'image/jpeg',
        'image/png',
        'image/webp'
    }

    # Configurações de Imagem
    IMAGE_SETTINGS = {
        'max_size': (1600, 1600),          # Tamanho máximo em pixels (largura, altura)
        'thumbnail_size': (400, 400),       # Tamanho das miniaturas
        'quality': 90,                      # Qualidade da imagem principal (0-100)
        'thumbnail_quality': 80,            # Qualidade da miniatura
        'compression_level': 6,             # Nível de compressão (0-9)
        'dpi': (300, 300),                  # Resolução da imagem
        'allowed_formats': {                # Formatos suportados para processamento
            'jpg': 'JPEG',
            'jpeg': 'JPEG',
            'png': 'PNG',
            'webp': 'WEBP'
        },
        'default_format': 'webp',           # Formato padrão para conversão
        'max_file_size': 16 * 1024 * 1024   # 16MB
    }

    # Configurações do Flask
    MAX_CONTENT_LENGTH = IMAGE_SETTINGS['max_file_size']
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False

    # Configurações de Cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # Configurações do Administrador
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or uuid4().hex  # Gera uma senha aleatória se não definida

    @staticmethod
    def init_app(app):
        """Método para inicialização adicional da aplicação"""
        # Garante que todas as pastas necessárias existam
        for folder in [Config.UPLOAD_FOLDER, Config.THUMBNAIL_FOLDER, Config.PROCESSED_FOLDER]:
            os.makedirs(folder, exist_ok=True)