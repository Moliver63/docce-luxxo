import os

class Config:
    # Configuração do banco de dados
    SQLALCHEMY_DATABASE_URI = 'sqlite:///joias.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pasta de upload
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    THUMBNAIL_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'thumbnails')

    # Chave secreta para segurança
    SECRET_KEY = 'sua_chave_secreta_aqui'

    # Extensões permitidas para upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Configurações de dimensionamento de imagens
    IMAGE_SETTINGS = {
        'max_size': (1200, 1200),          # Tamanho máximo (largura, altura)
        'thumbnail_size': (300, 300),       # Tamanho da miniatura
        'quality': 85,                      # Qualidade da imagem (0-100)
        'thumbnail_quality': 75,            # Qualidade da miniatura
        'allowed_formats': {                # Formatos suportados para redimensionamento
            'jpg': 'JPEG',
            'jpeg': 'JPEG',
            'png': 'PNG'
        }
    }

    # Tamanho máximo do arquivo (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024