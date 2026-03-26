from django.urls import path
from . import views

urlpatterns = [
    # URLs públicas - Home e escolha
    path('', views.index, name='index'),
    path('escolher-tarot/', views.escolher_tarot, name='escolher_tarot'),
    path('escolher-intencao/', views.escolher_intencao_feitico, name='escolher_intencao_feitico'),
    
    # URLs públicas - Agendamento
    path('agendar-produto/', views.agendar_produto, name='agendar_produto'),
    path('pagamento/<int:pk>/', views.pagamento, name='pagamento'),
    path('confirmar-pagamento/<int:pk>/', views.confirmar_pagamento, name='confirmar_pagamento'),
    path('confirmacao/<int:pk>/', views.confirmacao, name='confirmacao'),
    
    # URLs públicas - Acesso restrito para feitiços
    path('feiticos/<str:token>/', views.acessar_feiticos, name='comprar_feitico'),
    path('agendar-feitico/<str:token>/', views.agendar_feitico, name='agendar_feitico'),
    
    # API
    path('api/datas-disponiveis/', views.obter_datas_disponiveis, name='obter_datas_disponiveis'),
    
    # URLs administrativas customizadas
    path('painel/login/', views.admin_login, name='admin_login'),
    path('painel/logout/', views.admin_logout, name='admin_logout'),
    path('painel/', views.admin_painel, name='admin_painel'),
    path('painel/agendamentos/', views.admin_agendamentos, name='admin_agendamentos'),
    path('painel/agendamentos/<int:pk>/editar/', views.admin_editar_agendamento, name='admin_editar_agendamento'),
    path('painel/indisponibilidade/', views.admin_indisponibilidade, name='admin_indisponibilidade'),
    path('painel/gerenciar-produtos/', views.admin_gerenciar_produtos, name='admin_gerenciar_produtos'),
    path('admin/painel/', views.admin_painel, name='admin_dashboard'),  # Rota compatível
]
