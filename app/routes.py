from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Joia, Admin, Pedido, JoiaPedido, Pagamento, ConversaoMoeda, db
import hmac
import hashlib
import os
from config import Config
import requests
from datetime import datetime, timedelta
import uuid

# Initialize Blueprints
main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__, url_prefix='/admin')

# Helper Functions
def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def criar_cliente(nome, email, cpf_cnpj, telefone):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.ASAAS_API_KEY}"
        }
        payload = {
            "name": nome,
            "email": email,
            "cpfCnpj": cpf_cnpj,
            "phone": telefone,
            "notificationDisabled": True
        }
        response = requests.post(f"{Config.ASAAS_API_URL}/customers", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f"Erro ao criar cliente no Asaas: {str(e)}"
        if hasattr(e, 'response') and e.response:
            error_msg += f" - Resposta: {e.response.text}"
        return {"error": error_msg, "status_code": getattr(e.response, 'status_code', 500)}

def criar_cobranca(customer_id, valor, descricao, tipo="PIX", dias_vencimento=1):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.ASAAS_API_KEY}"
        }
        vencimento = (datetime.now() + timedelta(days=dias_vencimento)).strftime("%Y-%m-%d")
        payload = {
            "customer": customer_id,
            "billingType": tipo,
            "value": float(valor),
            "dueDate": vencimento,
            "description": descricao[:255],
            "externalReference": str(uuid.uuid4()),
            "postalService": False
        }
        if tipo == "PIX":
            payload["pixExpirationDate"] = (datetime.now() + timedelta(days=3)).isoformat()
        response = requests.post(f"{Config.ASAAS_API_URL}/payments", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f"Erro ao criar cobrança no Asaas: {str(e)}"
        if hasattr(e, 'response') and e.response:
            error_msg += f" - Resposta: {e.response.text}"
        return {"error": error_msg, "status_code": getattr(e.response, 'status_code', 500)}

def converter_para_usdt(valor_brl, pedido_id):
    taxa_conversao = 5.0  # Taxa fictícia
    valor_usdt = valor_brl / taxa_conversao
    conversao = ConversaoMoeda(valor_brl=valor_brl, valor_usdt=valor_usdt, taxa_conversao=taxa_conversao)
    db.session.add(conversao)
    db.session.commit()
    return True

def atualizar_pedido(pedido_id, status):
    pedido = Pedido.query.filter_by(external_reference=pedido_id).first()
    if pedido:
        pedido.status = status
        db.session.commit()
        return True
    return False

def enviar_email_confirmacao(pedido_id, valor):
    print(f"Enviando e-mail de confirmação para o pedido {pedido_id} no valor de R$ {valor}")
    return True

def handle_error(message, status_code=500):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response

# Public Routes
@main.route('/')
def index():
    try:
        joias = Joia.query.all()
        return render_template('index.html', joias=joias)
    except Exception as e:
        flash('Error loading homepage.', 'danger')
        return render_template('index.html', joias=[])

@main.route('/criar-pagamento', methods=['POST'])
def criar_pagamento():
    try:
        dados = request.get_json()
        required_fields = ['nome', 'email', 'cpf_cnpj', 'telefone', 'valor', 'descricao']
        if not all(field in dados for field in required_fields):
            return handle_error("Campos obrigatórios faltando", 400)
        
        cliente = criar_cliente(
            dados['nome'],
            dados['email'],
            dados['cpf_cnpj'],
            dados['telefone']
        )
        
        if "error" in cliente:
            return handle_error(cliente["error"], cliente.get("status_code", 500))
        
        cobranca = criar_cobranca(
            cliente["id"],
            dados["valor"],
            dados["descricao"],
            dados.get("tipo_pagamento", "PIX")
        )
        
        if "error" in cobranca:
            return handle_error(cobranca["error"], cobranca.get("status_code", 500))
        
        resposta = {
            "success": True,
            "payment_id": cobranca["id"],
            "customer_id": cliente["id"],
            "status": cobranca.get("status", "PENDING")
        }
        
        if cobranca["billingType"] == "PIX":
            resposta.update({
                "pix_qr_code": cobranca.get("encodedImage"),
                "pix_key": cobranca.get("payload"),
                "expiration_date": cobranca.get("expirationDate")
            })
        elif cobranca["billingType"] == "BOLETO":
            resposta.update({
                "boleto_url": cobranca.get("bankSlipUrl"),
                "barcode": cobranca.get("barCode")
            })
            
        return jsonify(resposta), 200
        
    except Exception as e:
        return handle_error(f"Erro interno no servidor: {str(e)}", 500)

# Admin Routes
@admin.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
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
    
    return render_template('admin/login.html')

@admin.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash('You have been logged out.', 'info')
    except Exception as e:
        flash('Error during logout.', 'danger')
    return redirect(url_for('main.index'))

@admin.route('/dashboard')
@login_required
def dashboard():
    try:
        joias = Joia.query.order_by(Joia.id.desc()).all()
        total_joias = len(joias)
        aneis_count = len([joia for joia in joias if joia.categoria == 'aneis'])
        brincos_count = len([joia for joia in joias if joia.categoria == 'brincos'])
        outros_count = len([joia for joia in joias if joia.categoria not in ['aneis', 'brincos']])
        
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
        
        precos = [joia.preco for joia in joias]
        max_preco = max(precos) if precos else 0
        min_preco = min(precos) if precos else 0
        avg_preco = (sum(precos) / len(precos)) if precos else 0
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
            required_fields = ['nome', 'preco', 'descricao', 'categoria']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'The {field} field is required.', 'danger')
                    return redirect(url_for('admin.upload'))
            
            if 'foto' not in request.files:
                flash('No file uploaded.', 'danger')
                return redirect(url_for('admin.upload'))
            
            foto = request.files['foto']
            if foto.filename == '':
                flash('No file selected.', 'danger')
                return redirect(url_for('admin.upload'))
            
            if not allowed_file(foto.filename):
                flash('Invalid file type. Only JPG, JPEG, PNG allowed.', 'danger')
                return redirect(url_for('admin.upload'))
            
            filename = secure_filename(foto.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            foto.save(filepath)
            
            nova_joia = Joia(
                nome=request.form['nome'],
                preco=float(request.form['preco']),
                descricao=request.form['descricao'],
                categoria=request.form['categoria'],
                foto=f'uploads/{filename}'
            )
            
            db.session.add(nova_joia)
            db.session.commit()
            flash('Jewelry added successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error processing form. Please try again.', 'danger')
            return redirect(url_for('admin.upload'))
    
    return render_template('admin/upload.html')

@admin.route('/edit_joia/<int:joia_id>', methods=['GET', 'POST'])
@login_required
def edit_joia(joia_id):
    joia = Joia.query.get_or_404(joia_id)
    
    if request.method == 'POST':
        try:
            required_fields = ['nome', 'preco', 'descricao', 'categoria']
            if not all(request.form.get(field) for field in required_fields):
                flash('All fields are required.', 'danger')
                return redirect(url_for('admin.edit_joia', joia_id=joia.id))
            
            joia.nome = request.form['nome']
            joia.preco = float(request.form['preco'])
            joia.descricao = request.form['descricao']
            joia.categoria = request.form['categoria']
            
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto.filename != '':
                    if not allowed_file(foto.filename):
                        flash('Invalid file type. Only JPG, JPEG, PNG allowed.', 'danger')
                        return redirect(url_for('admin.edit_joia', joia_id=joia.id))
                    
                    if joia.foto:
                        old_filepath = os.path.join(Config.UPLOAD_FOLDER, joia.foto.split('/')[-1])
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                    
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
    try:
        joia = Joia.query.get_or_404(joia_id)
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
    return render_template('admin/profile.html')

@admin.route('/webhook/pagamento', methods=['POST'])
def webhook_pagamento():
    assinatura = request.headers.get('X-Asaas-Signature')
    if not assinatura:
        return handle_error("Assinatura não fornecida", 401)
    
    secret = Config.ASAAS_WEBHOOK_SECRET.encode()
    payload = request.data
    assinatura_esperada = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(assinatura, assinatura_esperada):
        return handle_error("Assinatura inválida", 401)
    
    try:
        data = request.get_json()
        evento = data.get('event')
        pagamento = data.get('payment', {})
        
        if evento == 'PAYMENT_RECEIVED':
            pedido = Pedido.query.filter_by(external_reference=pagamento.get('id')).first()
            if pedido:
                pedido.status = 'pago'
                db.session.commit()
                
                novo_pagamento = Pagamento(
                    pedido_id=pedido.id,
                    tipo_pagamento=pagamento.get('billingType'),
                    status_pagamento=pagamento.get('status'),
                    valor=pagamento.get('value'),
                    data_pagamento=datetime.strptime(pagamento['paymentDate'], '%Y-%m-%d') if pagamento.get('paymentDate') else None,
                    external_reference=pagamento.get('id'),
                    qr_code=pagamento.get('encodedImage')
                )
                
                db.session.add(novo_pagamento)
                db.session.commit()
                
                if pedido.valor_total > 0:
                    converter_para_usdt(pedido.valor_total, pedido.id)
                
                enviar_email_confirmacao(pedido.id, pedido.valor_total)
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        return handle_error(str(e), 500)
    
    