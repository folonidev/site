from django.db import models
from django.utils import timezone
from datetime import datetime, time

# Será carregado do banco de dados
FEITICOS_DISPONIVEIS = []

# Horários disponíveis (em formato de tupla: hora_inicio, hora_fim)
HORARIOS_DISPONIVEIS = [
    (8, 12),   # 08:00 - 12:00
    (14, 18),  # 14:00 - 18:00
]

# Dias da semana (0=segunda, 6=domingo)
DIAS_DISPONIVEIS = [0, 1, 2, 3, 4]  # Segunda a sexta


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


class IndisponibilidadeFeitico(models.Model):
    """Modelo para gerenciar indisponibilidade de datas/horas"""
    data = models.DateField(unique=True)
    dia_inteiro_indisponivel = models.BooleanField(
        default=False,
        help_text="Se marcado, o dia inteiro fica indisponível"
    )
    horas_indisponiveis = models.JSONField(
        default=list, 
        blank=True, 
        help_text="Lista de horas indisponíveis (ex: [8, 9, 10])"
    )
    
    class Meta:
        verbose_name = 'Indisponibilidade de Feitiço'
        verbose_name_plural = 'Indisponibilidades de Feitiços'
        ordering = ['data']
    
    def __str__(self):
        if self.dia_inteiro_indisponivel:
            return f"{self.data} - Dia Inteiro Indisponível"
        return f"{self.data} - Horas Indisponíveis: {self.horas_indisponiveis}"


class Feitico(models.Model):
    """Modelo para armazenar solicitações de feiticos"""
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Pagamento'),
        ('pago', 'Pagamento Confirmado'),
        ('realizado', 'Feitico Realizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Dados do cliente
    nome = models.CharField(max_length=150)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    
    # Dados do feitico
    tipo_feitico = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    data_agendamento = models.DateField()
    hora_agendamento = models.TimeField()
    
    # Pagamento e status
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_pagamento = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Feitico'
        verbose_name_plural = 'Feiticos'
    
    def __str__(self):
        return f"{self.nome} - {self.tipo_feitico} ({self.data_agendamento})"
    
    def marcar_como_pago(self):
        """Marca o feitico como pago"""
        self.status = 'pago'
        self.data_pagamento = timezone.now()
        self.save()
    
    @property
    def esta_agendado(self):
        """Verifica se o feitico está agendado para o futuro"""
        agora = datetime.now().date()
        return self.data_agendamento >= agora
    
    @staticmethod
    def obter_preco_feitico(tipo_feitico):
        """Obtém o preço de um tipo de feitiço"""
        return TipoFeitico.obter_preco(tipo_feitico)
    
    @staticmethod
    def obter_feiticos_disponiveis():
        """Retorna lista de feitiços disponíveis"""
        return list(TipoFeitico.obter_feiticos_disponiveis())
    
    @staticmethod
    def verificar_disponibilidade(data, hora):
        """Verifica se data e hora estão disponíveis"""
        # Verificar se é dia da semana (segunda a sexta)
        if data.weekday() not in DIAS_DISPONIVEIS:
            return False, "Feitiços apenas de segunda a sexta"
        
        # Verificar indisponibilidades específicas
        try:
            indisp = IndisponibilidadeFeitico.objects.get(data=data)
            
            # Se o dia inteiro está indisponível
            if indisp.dia_inteiro_indisponivel:
                return False, "Este dia está indisponível. Por favor, selecione outro dia."
            
            # Se a hora específica está indisponível
            if hora.hour in indisp.horas_indisponiveis:
                return False, "Este horário está indisponível"
        except IndisponibilidadeFeitico.DoesNotExist:
            pass  # Usar disponibilidade padrão
        
        # Verificar se está dentro dos horários permitidos
        hora_permitida = False
        for inicio, fim in HORARIOS_DISPONIVEIS:
            if inicio <= hora.hour < fim:
                hora_permitida = True
                break
        
        if not hora_permitida:
            return False, "Horário fora do disponível (08-12 ou 14-18)"
        
        # Verificar se já existe feitiço agendado nesse horário
        feiticos_conflito = Feitico.objects.filter(
            data_agendamento=data,
            hora_agendamento=hora,
            status__in=['pago', 'realizado']
        )
        
        if feiticos_conflito.exists():
            return False, "Este horário já está ocupado"
        
        return True, "Disponível"
