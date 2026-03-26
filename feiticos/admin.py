from django.contrib import admin
from .models import Agendamento, IndisponibilidadeFeitico, TipoFeitico, TipoTarot


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo_produto', 'nome_produto', 'data_agendamento', 'status', 'valor', 'criado_em')
    list_filter = ('tipo_produto', 'status', 'data_agendamento', 'criado_em')
    search_fields = ('nome', 'email', 'telefone', 'nome_produto')
    readonly_fields = ('criado_em', 'atualizado_em', 'data_pagamento', 'token_acesso')
    
    fieldsets = (
        ('Dados do Cliente', {
            'fields': ('nome', 'email', 'telefone')
        }),
        ('Dados do Agendamento', {
            'fields': ('tipo_produto', 'nome_produto', 'descricao', 'data_agendamento')
        }),
        ('Pagamento e Status', {
            'fields': ('valor', 'status', 'data_pagamento')
        }),
        ('Acesso Restrito', {
            'fields': ('token_acesso', 'intencao_relacionada'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('nome', 'email', 'telefone', 'tipo_produto', 'nome_produto', 'descricao', 'data_agendamento', 'valor')
        return self.readonly_fields


@admin.register(IndisponibilidadeFeitico)
class IndisponibilidadeFeiticoAdmin(admin.ModelAdmin):
    list_display = ('data', 'indisponivel')
    list_filter = ('indisponivel', 'data')
    search_fields = ('data',)
    date_hierarchy = 'data'
    
    fieldsets = (
        ('Data', {
            'fields': ('data',)
        }),
        ('Status', {
            'fields': ('indisponivel',),
        }),
    )


@admin.register(TipoFeitico)
class TipoFeiticoAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'nome', 'preco', 'ativo', 'criado_em')
    list_filter = ('ativo', 'criado_em')
    search_fields = ('nome',)
    readonly_fields = ('criado_em',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'emoji', 'preco')
        }),
        ('Descrição', {
            'fields': ('descricao',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Timestamps', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TipoTarot)
class TipoTarotAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'nome', 'preco', 'ativo', 'criado_em')
    list_filter = ('ativo', 'criado_em')
    search_fields = ('nome',)
    readonly_fields = ('criado_em',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'emoji', 'preco')
        }),
        ('Descrição', {
            'fields': ('descricao',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Timestamps', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )
