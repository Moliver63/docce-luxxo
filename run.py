from app import create_app, db
from app.models import Admin

app = create_app()

def initialize_database():
    with app.app_context():
        print("Criando tabelas no banco de dados...")
        db.create_all()
        print("Tabelas criadas com sucesso!")
        
        # Criar usuário administrador padrão se não existir
        if not Admin.query.first():
            print("Criando usuário administrador padrão...")
            admin = Admin(username='admin')
            admin.set_password('admin123')  # Senha padrão - altere em produção!
            db.session.add(admin)
            db.session.commit()
            print("Usuário administrador criado com sucesso!")
            print(f"Username: admin\nPassword: admin123")
        else:
            print("Usuário administrador já existe no banco de dados.")

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)