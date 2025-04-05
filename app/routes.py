from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Joia, Admin, db
import os
import uuid  # Adicione esta linha
from config import Config

# Initialize Blueprints - keeping your original names
main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__, url_prefix='/admin')

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Public Routes
@main.route('/')
def index():
    """Homepage showing all jewelry items"""
    try:
        joias = Joia.query.all()
        return render_template('index.html', joias=joias)
    except Exception as e:
        flash('Error loading homepage.', 'danger')
        return render_template('index.html', joias=[])

# Admin Routes
@admin.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login route"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please fill in all fields.', 'danger')
                return redirect(url_for('admin.login'))
                
            admin_user = Admin.query.filter_by(username=username).first()
            
            if admin_user and admin_user.check_password(password):
                login_user(admin_user)
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('admin.dashboard'))
            else:
                flash('Invalid credentials. Please try again.', 'danger')
        except Exception as e:
            flash('An error occurred during login.', 'danger')
    
    return render_template('admin/login.html')

@admin.route('/logout')
@login_required
def logout():
    """Admin logout route"""
    try:
        logout_user()
        flash('You have been logged out.', 'info')
    except Exception as e:
        flash('Error during logout.', 'danger')
    return redirect(url_for('main.index'))

@admin.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    try:
        # 查询所有珠宝
        joias = Joia.query.order_by(Joia.id.desc()).all()
        
        # 计算各类别的珠宝数量
        total_joias = len(joias)
        aneis_count = len([joia for joia in joias if joia.categoria == 'aneis'])
        brincos_count = len([joia for joia in joias if joia.categoria == 'brincos'])
        outros_count = len([joia for joia in joias if joia.categoria not in ['aneis', 'brincos']])
        
        # 按类别分组
        categorias = [
            {
                'nome': 'aneis',
                'quantidade': aneis_count,
                'joias': [joia for joia in joias if joia.categoria == 'aneis'][:4]
            },
            {
                'nome': 'brincos',
                'quantidade': brincos_count,
                'joias': [joia for joia in joias if joia.categoria == 'brincos'][:4]
            },
            {
                'nome': 'outros',
                'quantidade': outros_count,
                'joias': [joia for joia in joias if joia.categoria not in ['aneis', 'brincos']] or []
            }
        ]
        
        # 计算价格统计
        precos = [joia.preco for joia in joias]
        max_preco = max(precos) if precos else 0
        min_preco = min(precos) if precos else 0
        avg_preco = (sum(precos) / len(precos)) if precos else 0
        
        # 按价格排序的珠宝
        joias_mais_caras = sorted(joias, key=lambda x: x.preco, reverse=True)[:5]
        
        return render_template(
            'admin/dashboard.html', 
            joias=joias,
            total_joias=total_joias,
            aneis_count=aneis_count,
            brincos_count=brincos_count,
            outros_count=outros_count,
            categorias=categorias,
            max_preco=max_preco,
            min_preco=min_preco,
            avg_preco=avg_preco,
            joias_mais_caras=joias_mais_caras
        )
    except Exception as e:
        flash('Error loading dashboard.', 'danger')
        return render_template('admin/dashboard.html', joias=[])

@admin.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            # Verificar campos obrigatórios
            required_fields = ['nome', 'preco', 'descricao', 'categoria']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'O campo {field} é obrigatório', 'danger')
                    return redirect(request.url)
            
            # Verificar se o arquivo foi enviado
            if 'foto' not in request.files:
                flash('Nenhuma foto foi enviada', 'danger')
                return redirect(request.url)
            
            foto = request.files['foto']
            
            # Verificar se um arquivo foi selecionado
            if foto.filename == '':
                flash('Nenhuma foto selecionada', 'danger')
                return redirect(request.url)
            
            # Verificar extensão do arquivo
            allowed_extensions = {'jpg', 'jpeg', 'png'}
            if not ('.' in foto.filename and 
                   foto.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                flash('Formato de arquivo inválido. Use JPG, JPEG ou PNG', 'danger')
                return redirect(request.url)
            
            # Criar diretório se não existir
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            
            # Gerar nome único para o arquivo
            file_ext = foto.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
            
            # Salvar arquivo
            foto.save(filepath)
            
            # Criar nova joia
            nova_joia = Joia(
                nome=request.form['nome'],
                preco=float(request.form['preco']),
                descricao=request.form['descricao'],
                categoria=request.form['categoria'],
                foto=f'/uploads/{unique_filename}'  # Caminho relativo para acesso
            )
            
            db.session.add(nova_joia)
            db.session.commit()
            
            flash('Joia cadastrada com sucesso!', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar joia: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('admin/upload.html')

@admin.route('/edit_joia/<int:joia_id>', methods=['GET', 'POST'])
@login_required
def edit_joia(joia_id):
    """Route for editing existing jewelry items"""
    joia = Joia.query.get_or_404(joia_id)
    if request.method == 'POST':
        try:
            # Validação dos campos obrigatórios
            if not all(request.form.get(field) for field in ['nome', 'preco', 'descricao', 'categoria']):
                flash('All fields are required.', 'danger')
                return redirect(url_for('admin.edit_joia', joia_id=joia.id))
            
            # Atualiza informações básicas
            joia.nome = request.form['nome']
            joia.preco = float(request.form['preco'])
            joia.descricao = request.form['descricao']
            joia.categoria = request.form['categoria']
            
            # Processa uma nova imagem, se fornecida
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto.filename != '':
                    if not allowed_file(foto.filename):
                        flash('Invalid file type. Only JPG, JPEG, PNG allowed.', 'danger')
                        return redirect(url_for('admin.edit_joia', joia_id=joia.id))
                    
                    # Remove a imagem antiga, se existir
                    if joia.foto:
                        old_filename = joia.foto.split('/')[-1]
                        old_filepath = os.path.join(Config.UPLOAD_FOLDER, old_filename)
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                    
                    # Salva a nova imagem
                    filename = secure_filename(foto.filename)
                    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    foto.save(filepath)
                    joia.foto = f'/static/uploads/{filename}'
            
            db.session.commit()
            flash('Jewelry updated successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash('Error updating jewelry. Please try again.', 'danger')
            return redirect(url_for('admin.edit_joia', joia_id=joia.id))
    
    return render_template('admin/edit_joia.html', joia=joia)

@admin.route('/delete_joia/<int:joia_id>', methods=['POST'])
@login_required
def delete_joia(joia_id):
    """Route for deleting jewelry items"""
    try:
        joia = Joia.query.get_or_404(joia_id)
        
        # Remove a imagem associada, se existir
        if joia.foto:
            filepath = os.path.join(Config.UPLOAD_FOLDER, joia.foto.split('/')[-1])
            if os.path.exists(filepath):
                os.remove(filepath)
        
        db.session.delete(joia)
        db.session.commit()
        flash('Jewelry deleted successfully!', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash('Error deleting jewelry. Please try again.', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@admin.route('/profile')
@login_required
def profile():
    """Admin profile route"""
    return render_template('admin/profile.html')