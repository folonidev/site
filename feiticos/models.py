from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

# Constantes de vagas
VAGAS_FEITICO = 3
VAGAS_TAROT = 10  # Compartilhadas entre tarot e intenção
VAGAS_ACOMPANHAMENTO = 10  # Exclusivas para tarot de acompanhamento (apenas sexta)

# Dias disponíveis: segunda a quinta (0-3) e sexta (4)
DIAS_DISPONIVEIS = [0, 1, 2, 3, 4]  # Segunda a sexta

# Horários de atendimento
HORARIOS_ATENDIMENTO = {
    'segunda_quinta': '20:00 - 00:00',
    'sexta': '13:00 - 16:00'
}


class TipoFeitico(models.Model):
    """Modelo para gerenciar tipos de feitiços e preços"""
    nome = models.CharField(max_length=150, unique=True)
    emoji = models.CharField(max_length=10, default='🔮')
    preco = models.FloatField()
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tipo de Feitiço'
        verbose_name_plural = 'Tipos de Feitiços'
    
    def __str__(self):
        return f"{self.emoji} {self.nome} - R$ {self.preco:.2f}"
    
    @staticmethod
    def obter_feiticos_disponiveis():
        """Retorna lista de feitiços ativos"""
        feiticos = TipoFeitico.objects.all()
        resultado = []
        for f in feiticos:
            if f.ativo:
                try:
                    preco = float(f.preco)
                except (TypeError, ValueError):
                    preco = float(f.preco.to_decimal())
                resultado.append({'nome': f.nome, 'emoji': f.emoji, 'preco': preco})
        return resultado
    
    @staticmethod
    def obter_preco(nome):
        """Obtém o preço de um tipo de feitiço"""
        feitico = TipoFeitico.objects.filter(nome=nome).first()
        if feitico and feitico.ativo:
            try:
                return float(feitico.preco)
            except (TypeError, ValueError):
                return float(feitico.preco.to_decimal())
        return 99.90


class TipoTarot(models.Model):
    """Modelo para gerenciar tipos de tarot e preços"""
    nome = models.CharField(max_length=150, unique=True)
    emoji = models.CharField(max_length=10, default='🔮')
    preco = models.FloatField()
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tipo de Tarot'
        verbose_name_plural = 'Tipos de Tarot'
    
    def __str__(self):
        return f"{self.emoji} {self.nome} - R$ {self.preco:.2f}"
    
    @staticmethod
    def obter_tarots_disponiveis():
        """Retorna lista de tarots ativos"""
        tarots = TipoTarot.objects.all()
        resultado = []
        for t in tarots:
            if t.ativo:
                try:
                    preco = float(t.preco)
                except (TypeError, ValueError):
                    preco = float(t.preco.to_decimal())
                resultado.append({'nome': t.nome, 'emoji': t.emoji, 'preco': preco})
        return resultado


class IndisponibilidadeFeitico(models.Model):
    """Modelo para gerenciar indisponibilidade de datas"""
    data = models.DateField(unique=True)
    indisponivel = models.BooleanField(
        default=False,
        help_text="Se marcado, este dia fica indisponível"
    )
    
    class Meta:
        verbose_name = 'Indisponibilidade'
        verbose_name_plural = 'Indisponibilidades'
        ordering = ['data']
    
    def __str__(self):
        return f"{self.data} - {'Indisponível' if self.indisponivel else 'Disponível'}"


class Agendamento(models.Model):
    """Modelo para armazenar agendamentos (feitiços, tarot, intenções)"""
    
    TIPO_PRODUTO_CHOICES = [
        ('tarot', 'Tiragem de Tarot'),
        ('tarot_acompanhamento', 'Tiragem de Acompanhamento'),
        ('intencao_feitico', 'Intenção de Feitiço'),
        ('feitico', 'Feitiço'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Pagamento'),
        ('aguardando_ml', 'Aguardando retorno ML'),
        ('pagamento_confirmado', 'Pagamento Confirmado'),
        ('pagamento_recusado', 'Pagamento Recusado'),
        ('enviar_link', 'Enviar Link para Cliente'),
        ('link_enviado', 'Link Enviado'),
        ('realizado', 'Realizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Dados do cliente
    nome = models.CharField(max_length=150)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    
    # Dados do agendamento
    tipo_produto = models.CharField(max_length=20, choices=TIPO_PRODUTO_CHOICES)
    nome_produto = models.CharField(max_length=200)  # Nome do feitiço, tarot ou intenção
    descricao = models.TextField(blank=True, null=True)
    data_agendamento = models.DateField()
    data_agendamento_original = models.DateField(blank=True, null=True, help_text="Data original do agendamento (para rastreabilidade)")
    
    # Pagamento e status
    valor = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_pagamento = models.DateTimeField(blank=True, null=True)
    
    # Link de acesso restrito (para feitiços após aprovação da intenção)
    token_acesso = models.CharField(max_length=100, blank=True, null=True)
    
    # Mercado Pago
    external_reference = models.CharField(max_length=100, blank=True, null=True, unique=True, help_text="ID externo do Mercado Pago para rastreamento")
    mercado_pago_payment_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID do pagamento no Mercado Pago")
    
    # Relacionamento com intenção (para feitiços)
    intencao_relacionada = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='feiticos_relacionados',
        help_text="Intenção de feitiço relacionada (se aplicável)"
    )
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Salva o agendamento e define data_agendamento_original se não existir"""
        if not self.data_agendamento_original:
            self.data_agendamento_original = self.data_agendamento
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
    
    def __str__(self):
        return f"{self.nome} - {self.tipo_produto} ({self.data_agendamento})"
    
    def gerar_token_acesso(self):
        """Gera um token de acesso único apenas se ainda não existir um"""
        if not self.token_acesso:
            self.token_acesso = str(uuid.uuid4())
            self.save()
        return self.token_acesso
    
    def marcar_como_pago(self):
        """Marca o agendamento como pago"""
        self.status = 'pagamento_confirmado'
        self.data_pagamento = timezone.now()
        self.save()
    
    def marcar_como_aprovado(self):
        """Marca intenção como aprovada e gera token para feitiço"""
        if self.tipo_produto == 'intencao_feitico':
            self.status = 'aprovado'
            self.gerar_token_acesso()
            self.save()
    
    @staticmethod
    def contar_vagas_usadas(data, tipo_produto):
        """Conta quantas vagas foram usadas em uma data"""
        # No MongoDB/Djongo, filtros de data e status__in podem ser instáveis
        # Buscamos todos os agendamentos daquela data e filtramos via Python para garantir estabilidade
        agendamentos = Agendamento.objects.filter(data_agendamento=data)
        count = 0
        status_validos = ['pagamento_confirmado', 'pago', 'enviar_link', 'link_enviado', 'realizado']
        for ag in agendamentos:
            if ag.tipo_produto == tipo_produto and ag.status in status_validos:
                count += 1
        return count
    
    @staticmethod
    def verificar_vagas_disponiveis(data, tipo_produto):
        """Verifica se há vagas disponíveis para um tipo de produto em uma data"""
        # Verificar indisponibilidade - Usando filter().first() para ser mais resiliente
        indisp = IndisponibilidadeFeitico.objects.filter(data=data).first()
        if indisp and indisp.indisponivel:
            return False, "Este dia está indisponível"
        
        # Tarot de acompanhamento: APENAS SEXTA (dia 4)
        if tipo_produto == 'tarot_acompanhamento':
            if data.weekday() != 4:  # 4 = sexta-feira
                return False, "Tiragem de acompanhamento disponível apenas na sexta-feira"
            vagas_usadas = Agendamento.contar_vagas_usadas(data, 'tarot_acompanhamento')
            vagas_disponiveis = VAGAS_ACOMPANHAMENTO - vagas_usadas
            if vagas_disponiveis <= 0:
                return False, "Sem vagas disponíveis para acompanhamento nesta sexta"
            return True, f"{vagas_disponiveis} vagas disponíveis"
        
        # Feitiço final: 3 vagas exclusivas (segunda a sexta)
        if tipo_produto == 'feitico':
            if data.weekday() not in DIAS_DISPONIVEIS:
                return False, "Atendimento apenas de segunda a sexta"
            vagas_usadas = Agendamento.contar_vagas_usadas(data, 'feitico')
            vagas_disponiveis = VAGAS_FEITICO - vagas_usadas
            if vagas_disponiveis <= 0:
                return False, "Sem vagas disponíveis para feitiços nesta data"
            return True, f"{vagas_disponiveis} vagas disponíveis"
        
        # Tarot e Intenção: compartilham 10 vagas (segunda a sexta)
        if tipo_produto in ['tarot', 'intencao_feitico']:
            if data.weekday() not in DIAS_DISPONIVEIS:
                return False, "Atendimento apenas de segunda a sexta"
            vagas_tarot = Agendamento.contar_vagas_usadas(data, 'tarot')
            vagas_intencao = Agendamento.contar_vagas_usadas(data, 'intencao_feitico')
            vagas_usadas = vagas_tarot + vagas_intencao
            vagas_disponiveis = VAGAS_TAROT - vagas_usadas
            if vagas_disponiveis <= 0:
                return False, "Sem vagas disponíveis para tarot/intenção nesta data"
            return True, f"{vagas_disponiveis} vagas disponíveis"
        
        return False, "Tipo de produto inválido"


class WebhookMercadoPago(models.Model):
    """Modelo para armazenar webhooks recebidos do Mercado Pago"""
    
    STATUS_WEBHOOK_CHOICES = [
        ('recebido', 'Recebido'),
        ('processado', 'Processado'),
        ('erro', 'Erro'),
    ]
    
    # Dados do webhook
    external_reference = models.CharField(max_length=100, help_text="ID externo do agendamento")
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    topic = models.CharField(max_length=50, help_text="Tipo de notificação (payment, merchant_order, etc)")
    
    # Status do pagamento no MP
    payment_status = models.CharField(max_length=50, blank=True, null=True, help_text="Status do pagamento (approved, pending, rejected, etc)")
    
    # Dados brutos do webhook
    payload = models.JSONField(help_text="Payload completo do webhook")
    
    # Status de processamento
    status = models.CharField(max_length=20, choices=STATUS_WEBHOOK_CHOICES, default='recebido')
    erro_mensagem = models.TextField(blank=True, null=True)
    
    # Relacionamento com agendamento
    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='webhooks_mercado_pago'
    )
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    processado_em = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Webhook Mercado Pago'
        verbose_name_plural = 'Webhooks Mercado Pago'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Webhook {self.topic} - {self.external_reference} ({self.status})"
