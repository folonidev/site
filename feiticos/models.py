from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

# Constantes de vagas
VAGAS_FEITICO = 3
VAGAS_TAROT = 10

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
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tipo de Feitiço'
        verbose_name_plural = 'Tipos de Feitiços'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.emoji} {self.nome} - R$ {self.preco:.2f}"
    
    @staticmethod
    def obter_feiticos_disponiveis():
        """Retorna lista de feitiços ativos"""
        return TipoFeitico.objects.filter(ativo=True).values('nome', 'emoji', 'preco')
    
    @staticmethod
    def obter_preco(nome):
        """Obtém o preço de um tipo de feitiço"""
        try:
            feitico = TipoFeitico.objects.get(nome=nome, ativo=True)
            return float(feitico.preco)
        except TipoFeitico.DoesNotExist:
            return 99.90


class TipoTarot(models.Model):
    """Modelo para gerenciar tipos de tarot e preços"""
    nome = models.CharField(max_length=150, unique=True)
    emoji = models.CharField(max_length=10, default='🔮')
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tipo de Tarot'
        verbose_name_plural = 'Tipos de Tarot'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.emoji} {self.nome} - R$ {self.preco:.2f}"
    
    @staticmethod
    def obter_tarots_disponiveis():
        """Retorna lista de tarots ativos"""
        return TipoTarot.objects.filter(ativo=True).values('nome', 'emoji', 'preco')


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
        ('intencao_feitico', 'Intenção de Feitiço'),
        ('feitico', 'Feitiço'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Pagamento'),
        ('pagamento_confirmado', 'Pagamento Confirmado'),
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
    
    # Pagamento e status
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_pagamento = models.DateTimeField(blank=True, null=True)
    
    # Link de acesso restrito (para feitiços após aprovação da intenção)
    token_acesso = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
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
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
    
    def __str__(self):
        return f"{self.nome} - {self.tipo_produto} ({self.data_agendamento})"
    
    def gerar_token_acesso(self):
        """Gera um token de acesso único"""
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
        return Agendamento.objects.filter(
            data_agendamento=data,
            tipo_produto=tipo_produto,
            status__in=['pagamento_confirmado', 'pago', 'enviar_link', 'link_enviado', 'realizado']
        ).count()
    
    @staticmethod
    def verificar_vagas_disponiveis(data, tipo_produto):
        """Verifica se há vagas disponíveis para um tipo de produto em uma data"""
        # Verificar se é dia válido
        if data.weekday() not in DIAS_DISPONIVEIS:
            return False, "Atendimento apenas de segunda a sexta"
        
        # Verificar indisponibilidade
        try:
            indisp = IndisponibilidadeFeitico.objects.get(data=data)
            if indisp.indisponivel:
                return False, "Este dia está indisponível"
        except IndisponibilidadeFeitico.DoesNotExist:
            pass
        
        # Feitiço final: 3 vagas exclusivas
        if tipo_produto == 'feitico':
            vagas_usadas = Agendamento.contar_vagas_usadas(data, 'feitico')
            vagas_disponiveis = VAGAS_FEITICO - vagas_usadas
            if vagas_disponiveis <= 0:
                return False, "Sem vagas disponíveis para feitiços nesta data"
            return True, f"{vagas_disponiveis} vagas disponíveis"
        
        # Tarot e Intenção: compartilham 10 vagas
        if tipo_produto in ['tarot', 'intencao_feitico']:
            vagas_tarot = Agendamento.contar_vagas_usadas(data, 'tarot')
            vagas_intencao = Agendamento.contar_vagas_usadas(data, 'intencao_feitico')
            vagas_usadas = vagas_tarot + vagas_intencao
            vagas_disponiveis = VAGAS_TAROT - vagas_usadas
            if vagas_disponiveis <= 0:
                return False, "Sem vagas disponíveis para tarot/intenção nesta data"
            return True, f"{vagas_disponiveis} vagas disponíveis"
        
        return False, "Tipo de produto inválido"
