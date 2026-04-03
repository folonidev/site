"""
Utilitaríos para integração com Mercado Pago
"""
import mercadopago
import requests
from django.conf import settings
from decouple import config

# ⚠️ Credenciais do Mercado Pago (OBRIGATÓRIO estar em .env)
MP_ACCESS_TOKEN = config('MERCADO_PAGO_ACCESS_TOKEN')

# ⚠️ URLs de retorno (OBRIGATÓRIO estar em .env)
BACK_URL_SUCCESS = config('MERCADO_PAGO_BACK_URL_SUCCESS')
BACK_URL_FAILURE = config('MERCADO_PAGO_BACK_URL_FAILURE')
BACK_URL_PENDING = config('MERCADO_PAGO_BACK_URL_PENDING')
GENERIC_BACK_URL = config('MERCADO_PAGO_BACK_URL_SUCCESS')

# ⚠️ Webhook URL (OBRIGATÓRIO estar em .env)
WEBHOOK_URL = config('MERCADO_PAGO_WEBHOOK_URL')


def criar_preferencia_mercado_pago(agendamento, back_url_override=None):
    """
    Cria uma preferência de pagamento no Mercado Pago
    
    Args:
        agendamento: Objeto Agendamento do Django
        back_url_override: URL de retorno customizada (opcional)
    
    Returns:
        dict com os dados da preferência ou None se houver erro
    """
    try:
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        
        # Preparar dados da preferência
        preference_data = {
            "items": [
                {
                    "title": f"{agendamento.nome_produto}",
                    "description": f"Agendamento para {agendamento.data_agendamento.strftime('%d/%m/%Y')}",
                    "quantity": 1,
                    "unit_price": float(agendamento.valor),
                }
            ],
            "payer": {
                "name": agendamento.nome,
                "email": agendamento.email,
                "phone": {
                    "number": agendamento.telefone
                }
            },
            "external_reference": str(agendamento.external_reference),
        }
        
        # Adicionar back_urls com URLs específicas
        # O MP valida que as URLs existem e retornam HTTP 200
        # Todas as URLs apontam para a mesma página de processamento, mas com status diferente
        base_url = BACK_URL_SUCCESS.split('?')[0]  # Remove query params se houver
        preference_data["back_urls"] = {
            "success": f"{base_url}?external_reference={agendamento.external_reference}&status=approved",
            "failure": f"{base_url}?external_reference={agendamento.external_reference}&status=rejected",
            "pending": f"{base_url}?external_reference={agendamento.external_reference}&status=pending"
        }
        
        # Adicionar notification_url para receber webhooks
        notification_url = WEBHOOK_URL
        if notification_url:
            preference_data["notification_url"] = notification_url
        
        # Criar preferência
        print("\n" + "="*80)
        print(f"[MP_API] Criando preferencia com external_reference: {agendamento.external_reference}")
        print(f"[MP_API] Dados enviados:")
        print(f"  - external_reference: {preference_data.get('external_reference')}")
        print(f"  - valor: {preference_data['items'][0]['unit_price']}")
        print("="*80 + "\n")
        
        preference_response = sdk.preference().create(preference_data)
        
        print("\n" + "="*80)
        print(f"[MP_API] Status HTTP: {preference_response['status']}")
        print(f"[MP_API] Response completo:")
        print(preference_response)
        print("="*80 + "\n")
        
        if preference_response["status"] == 201:
            response = preference_response["response"]
            print("\n" + "="*80)
            print(f"[MP_API] Preferencia criada com sucesso!")
            print(f"  - id: {response.get('id')}")
            print(f"  - external_reference: {response.get('external_reference')}")
            print(f"  - init_point: {response.get('init_point')}")
            print("="*80 + "\n")
            return response
        else:
            print(f"Erro ao criar preferência: {preference_response}")
            return None
            
    except Exception as e:
        print(f"Erro ao criar preferência do Mercado Pago: {str(e)}")
        return None


def verificar_status_pagamento(payment_id):
    """
    Verifica o status de um pagamento no Mercado Pago via GET
    
    Args:
        payment_id: ID do pagamento no Mercado Pago
    
    Returns:
        dict com os dados do pagamento ou None se houver erro
    """
    try:
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        
        print("\n" + "="*80)
        print(f"[MP_API] Chamando sdk.payment().get({payment_id})")
        print("="*80 + "\n")
        
        payment_response = sdk.payment().get(payment_id)
        
        print("\n" + "="*80)
        print(f"[MP_API] Status HTTP: {payment_response['status']}")
        print(f"[MP_API] Response completo:")
        print(payment_response)
        print("="*80 + "\n")
        
        if payment_response["status"] == 200:
            response_data = payment_response["response"]
            print("\n" + "="*80)
            print(f"[MP_API] TODOS OS CAMPOS DA RESPOSTA:")
            print("="*80)
            for key, value in response_data.items():
                print(f"  {key}: {value}")
            print("="*80)
            print(f"[MP_API] Dados extraidos:")
            print(f"  - external_reference: {response_data.get('external_reference')}")
            print(f"  - status: {response_data.get('status')}")
            print(f"  - id: {response_data.get('id')}")
            print("="*80 + "\n")
            return response_data
        else:
            print(f"Erro ao verificar pagamento: {payment_response}")
            return None
            
    except Exception as e:
        print(f"Erro ao verificar status do pagamento: {str(e)}")
        return None


def extrair_dados_webhook(payload):
    """
    Extrai dados relevantes do webhook do Mercado Pago
    
    Args:
        payload: Dados brutos do webhook
    
    Returns:
        dict com dados extraídos
    """
    try:
        data = {
            'topic': payload.get('topic'),
            'resource': payload.get('resource'),
            'data_id': payload.get('data', {}).get('id'),
        }
        
        # Se for notificação de pagamento
        if data['topic'] == 'payment':
            data['payment_id'] = data['data_id']
        
        # Se for notificação de merchant order
        elif data['topic'] == 'merchant_order':
            data['merchant_order_id'] = data['data_id']
        
        return data
        
    except Exception as e:
        print(f"Erro ao extrair dados do webhook: {str(e)}")
        return None


def mapear_status_mp_para_agendamento(status_mp):
    """
    Mapeia status do Mercado Pago para status do Agendamento
    
    Args:
        status_mp: Status retornado pelo Mercado Pago
    
    Returns:
        str com o status do agendamento
    """
    mapeamento = {
        'approved': 'pagamento_confirmado',  # Verde - Pagamento confirmado
        'pending': 'pendente',  # Amarelo - Aguardando processamento
        'authorized': 'pendente',  # Amarelo - Autorizado mas não capturado
        'in_process': 'pendente',  # Amarelo - Em processamento
        'in_mediation': 'pendente',  # Amarelo - Em mediação
        'rejected': 'pagamento_recusado',  # Vermelho - Pagamento recusado
        'cancelled': 'pagamento_recusado',  # Vermelho - Cancelado
        'refunded': 'pagamento_recusado',  # Vermelho - Reembolsado
        'charged_back': 'pagamento_recusado',  # Vermelho - Chargeback
    }
    
    return mapeamento.get(status_mp, 'pendente')  # Padrão: amarelo (pendente)
