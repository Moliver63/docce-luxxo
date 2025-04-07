import requests
from config import Config
from datetime import datetime, timedelta
import uuid
from flask import jsonify
from app.models import db, Pedido, Pagamento, ConversaoMoeda

class AsaasService:
    @staticmethod
    def criar_cliente(nome, email, cpf_cnpj, telefone):
        try:
            headers = {
                "Content-Type": "application/json",
                "access_token": Config.ASAAS_API_KEY
            }
            payload = {
                "name": nome,
                "email": email,
                "cpfCnpj": cpf_cnpj,
                "phone": telefone,
                "notificationDisabled": True
            }
            response = requests.post(
                f"{Config.ASAAS_API_URL}/customers",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro ao criar cliente no Asaas: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f" - Resposta: {e.response.text}"
            return {"error": error_msg, "status_code": getattr(e.response, 'status_code', 500)}

    @staticmethod
    def criar_cobranca(customer_id, valor, descricao, tipo="PIX", dias_vencimento=1):
        try:
            headers = {
                "Content-Type": "application/json",
                "access_token": Config.ASAAS_API_KEY
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
                
            response = requests.post(
                f"{Config.ASAAS_API_URL}/payments",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro ao criar cobrança no Asaas: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f" - Resposta: {e.response.text}"
            return {"error": error_msg, "status_code": getattr(e.response, 'status_code', 500)}

    @staticmethod
    def verificar_pagamento(payment_id):
        try:
            headers = {"access_token": Config.ASAAS_API_KEY}
            response = requests.get(
                f"{Config.ASAAS_API_URL}/payments/{payment_id}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro ao verificar pagamento: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f" - Resposta: {e.response.text}"
            return {"error": error_msg, "status_code": getattr(e.response, 'status_code', 500)}