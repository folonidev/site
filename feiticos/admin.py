from django.contrib import admin
from .models import Feitico, IndisponibilidadeFeitico, TipoFeitico


@admin.register(Feitico)
class FeiticoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo_feitico', 'data_agendamento', 'status', 'valor', 'criado_em')
    list_filter = ('status', 'data_agendamento', 'criado_em')
    search_fields = ('nome', 'email', 'telefone', 'tipo_feitico')
    readonly_fields = ('criado_em', 'atualizado_em', 'data_pagamento')
    
    fieldsets = (
        ('Dados do Cliente', {
            'fields': ('nome', 'email', 'telefone')
        }),
        ('Dados do Feitico', {
            'fields': ('tipo_feitico', 'descricao', 'data_agendamento', 'hora_agendamento')
        }),
        ('Pagamento e Status', {
            'fields': ('valor', 'status', 'data_pagamento')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('nome', 'email', 'telefone', 'tipo_feitico', 'descricao', 'data_agendamento', 'hora_agendamento', 'valor')
        return self.readonly_fields


@admin.register(IndisponibilidadeFeitico)
class IndisponibilidadeFeiticoAdmin(admin.ModelAdmin):
    list_display = ('data', 'dia_inteiro_indisponivel', 'horas_indisponiveis')
    list_filter = ('dia_inteiro_indisponivel', 'data')
    search_fields = ('data',)
    date_hierarchy = 'data'
    
    fieldsets = (
        ('Data', {
            'fields': ('data',)
        }),
        ('Indisponibilidade', {
            'fields': ('dia_inteiro_indisponivel', 'horas_indisponiveis'),
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
