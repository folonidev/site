"""
Utilitaríos para envio de emails via SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

# Configurações de SMTP (carregadas do .env via Django settings)
SMTP_SERVER = settings.EMAIL_HOST
SMTP_PORT = settings.EMAIL_PORT
SMTP_USER = settings.EMAIL_HOST_USER
SMTP_PASSWORD = settings.EMAIL_HOST_PASSWORD
EMAIL_FROM = settings.DEFAULT_FROM_EMAIL




def enviar_email_confirmacao_pagamento(agendamento, status_pagamento):
    """
    Envia email de confirmação de pagamento
    
    Args:
        agendamento: Objeto Agendamento
        status_pagamento: Status do pagamento ('approved', 'pending', 'rejected', etc)
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Credenciais de SMTP não configuradas")
        return False
    
    try:
        # Mapear status para mensagem
        status_mensagem = {
            'approved': 'APROVADO',
            'pending': 'PENDENTE',
            'rejected': 'RECUSADO',
            'cancelled': 'CANCELADO',
        }
        
        status_texto = status_mensagem.get(status_pagamento, 'EM PROCESSAMENTO')
        
        # Preparar email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Status do Pagamento - {agendamento.nome_produto}"
        msg['From'] = EMAIL_FROM
        msg['To'] = agendamento.email
        
        # Corpo do email em HTML
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                    .status {{ font-size: 24px; font-weight: bold; margin: 20px 0; }}
                    .status.approved {{ color: #28a745; }}
                    .status.pending {{ color: #ffc107; }}
                    .status.rejected {{ color: #dc3545; }}
                    .details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✨ Raízes Tarot e Magia Ancestral</h1>
                        <p>Status do Seu Pagamento</p>
                    </div>
                    
                    <p>Olá <strong>{agendamento.nome}</strong>,</p>
                    
                    <p>Recebemos sua solicitação de pagamento. Aqui está o status:</p>
                    
                    <div class="status {status_pagamento}">
                        Status: {status_texto}
                    </div>
                    
                    <div class="details">
                        <h3>Detalhes do Pedido</h3>
                        <p><strong>Produto:</strong> {agendamento.nome_produto}</p>
                        <p><strong>Valor:</strong> R$ {agendamento.valor:.2f}</p>
                        <p><strong>Data do Agendamento:</strong> {agendamento.data_agendamento.strftime('%d/%m/%Y')}</p>
                        <p><strong>Referência:</strong> {agendamento.external_reference}</p>
                    </div>
                    
                    {"<p style='color: #28a745; font-weight: bold;'>✅ Seu pagamento foi aprovado! Você receberá mais informações em breve.</p>" if status_pagamento == 'approved' else ""}
                    {"<p style='color: #ffc107; font-weight: bold;'>⏳ Seu pagamento está sendo processado. Atualizaremos você em breve.</p>" if status_pagamento == 'pending' else ""}
                    {"<p style='color: #dc3545; font-weight: bold;'>❌ Seu pagamento foi recusado. Por favor, tente novamente ou entre em contato conosco.</p>" if status_pagamento == 'rejected' else ""}
                    
                    <p>Se tiver dúvidas, entre em contato conosco.</p>
                    
                    <div class="footer">
                        <p>© 2026 Raízes Tarot e Magia Ancestral. Todos os direitos reservados.</p>
                        <p>Este é um email automático. Por favor, não responda.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Adicionar parte HTML
        part = MIMEText(html, 'html')
        msg.attach(part)
        
        # Enviar email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email enviado com sucesso para {agendamento.email}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False


def enviar_email_link_feitico(agendamento, link):
    """
    Envia email com link de acesso para o feitiço
    
    Args:
        agendamento: Objeto Agendamento
        link: URL do link de acesso
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Credenciais de SMTP não configuradas")
        return False
    
    try:
        # Preparar email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Seu Feitiço Está Pronto - {agendamento.nome_produto}"
        msg['From'] = EMAIL_FROM
        msg['To'] = agendamento.email
        
        # Corpo do email em HTML
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; border-radius: 5px; text-decoration: none; margin: 20px 0; font-weight: bold; }}
                    .details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✨ Raízes Tarot e Magia Ancestral</h1>
                        <p>Seu Feitiço Está Pronto!</p>
                    </div>
                    
                    <p>Olá <strong>{agendamento.nome}</strong>,</p>
                    
                    <p>Seu pagamento foi aprovado e seu feitiço está pronto para ser acessado!</p>
                    
                    <div class="details">
                        <h3>Detalhes do Seu Feitiço</h3>
                        <p><strong>Tipo:</strong> {agendamento.nome_produto}</p>
                        <p><strong>Data Agendada:</strong> {agendamento.data_agendamento.strftime('%d/%m/%Y')}</p>
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="{link}" class="button">🔗 Acessar Meu Feitiço</a>
                    </p>
                    
                    <p>O link acima o levará diretamente ao seu feitiço. Guarde-o com segurança!</p>
                    
                    <p>Se tiver dúvidas, entre em contato conosco.</p>
                    
                    <div class="footer">
                        <p>© 2026 Raízes Tarot e Magia Ancestral. Todos os direitos reservados.</p>
                        <p>Este é um email automático. Por favor, não responda.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Adicionar parte HTML
        part = MIMEText(html, 'html')
        msg.attach(part)
        
        # Enviar email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email com link enviado com sucesso para {agendamento.email}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False
