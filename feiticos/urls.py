from django.urls import path
from . import views

urlpatterns = [
    # URLs públicas
    path('', views.index, name='index'),
    path('agendar/', views.agendar_feitico, name='agendar_feitico'),
    path('pagamento/<int:pk>/', views.pagamento, name='pagamento'),
    path('confirmar-pagamento/<int:pk>/', views.confirmar_pagamento, name='confirmar_pagamento'),
    path('confirmacao/<int:pk>/', views.confirmacao, name='confirmacao'),
    path('api/horarios-disponiveis/', views.obter_horarios_disponiveis, name='obter_horarios_disponiveis'),
    
    # URLs administrativas customizadas
    path('painel/login/', views.admin_login, name='admin_login'),
    path('painel/logout/', views.admin_logout, name='admin_logout'),
    path('painel/', views.admin_painel, name='admin_painel'),
    path('painel/feiticos/', views.admin_feiticos, name='admin_feiticos'),
    path('painel/feiticos/<int:pk>/editar/', views.admin_editar_feitico, name='admin_editar_feitico'),
    path('painel/feiticos/<int:pk>/deletar/', views.admin_deletar_feitico, name='admin_deletar_feitico'),
    path('painel/disponibilidade/', views.admin_disponibilidade, name='admin_disponibilidade'),
    path('painel/gerenciar-feiticos/', views.admin_gerenciar_feiticos, name='admin_gerenciar_feiticos'),
    path('admin/painel/', views.admin_painel, name='admin_dashboard'),  # Rota compatível,
]
