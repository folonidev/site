from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from .models import Feitico, IndisponibilidadeFeitico, TipoFeitico, FEITICOS_DISPONIVEIS
import json
import re


def index(request):
    """Página inicial com formulário de agendamento"""
    feiticos = list(TipoFeitico.obter_feiticos_disponiveis())
    context = {
        'feiticos': feiticos,
    }
    return render(request, 'feiticos/index.html', context)


@require_http_methods(["POST"])
def agendar_feitico(request):
    """Processa o agendamento do feitiço"""
    try:
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        tipo_feitico = request.POST.get('tipo_feitico', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        data_agendamento = request.POST.get('data_agendamento', '').strip()
        hora_agendamento = request.POST.get('hora_agendamento', '').strip()
        
        # Validações básicas
        if not all([nome, email, telefone, tipo_feitico, data_agendamento, hora_agendamento]):
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
            return redirect('index')
        
        # Validar email
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            messages.error(request, 'Email inválido.')
            return redirect('index')
        
        # Validar data e hora
        try:
            data_obj = datetime.strptime(data_agendamento, '%Y-%m-%d').date()
            hora_obj = datetime.strptime(hora_agendamento, '%H:%M').time()
            
            if data_obj < datetime.now().date():
                messages.error(request, 'A data do feitiço não pode ser no passado.')
                return redirect('index')
        except ValueError:
            messages.error(request, 'Formato de data ou hora inválido.')
            return redirect('index')
        
        # Verificar disponibilidade
        disponivel, mensagem = Feitico.verificar_disponibilidade(data_obj, hora_obj)
        if not disponivel:
            messages.error(request, f'Indisponível: {mensagem}')
            return redirect('index')
        
        # Obter preço do feitiço
        valor = Feitico.obter_preco_feitico(tipo_feitico)
        
        # Criar feitiço
        feitico = Feitico.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            tipo_feitico=tipo_feitico,
            descricao=descricao,
            data_agendamento=data_obj,
            hora_agendamento=hora_obj,
            valor=valor,
        )
        
        # Redirecionar para pagamento
        return redirect('pagamento', pk=feitico.pk)
    
    except Exception as e:
        messages.error(request, f'Erro ao agendar feitiço: {str(e)}')
        return redirect('index')


def pagamento(request, pk):
    """Página de pagamento"""
    feitico = get_object_or_404(Feitico, pk=pk)
    
    if feitico.status != 'pendente':
        messages.warning(request, 'Este feitiço já foi processado.')
        return redirect('index')
    
    context = {
        'feitico': feitico,
    }
    return render(request, 'feiticos/pagamento.html', context)


@require_http_methods(["POST"])
def confirmar_pagamento(request, pk):
    """Simula a confirmação de pagamento (integração com Mercado Pago seria aqui)"""
    feitico = get_object_or_404(Feitico, pk=pk)
    
    if feitico.status != 'pendente':
        return JsonResponse({'erro': 'Feitiço já processado'}, status=400)
    
    # Aqui entraria a integração com Mercado Pago
    # Por enquanto, apenas simulamos o pagamento bem-sucedido
    feitico.marcar_como_pago()
    
    return JsonResponse({
        'sucesso': True,
        'mensagem': 'Pagamento confirmado! Seu feitiço foi agendado com sucesso.',
        'redirect': f'/confirmacao/{feitico.pk}/'
    })


def confirmacao(request, pk):
    """Página de confirmação após pagamento"""
    feitico = get_object_or_404(Feitico, pk=pk)
    
    if feitico.status != 'pago':
        messages.warning(request, 'Feitiço não foi pago ainda.')
        return redirect('index')
    
    context = {
        'feitico': feitico,
    }
    return render(request, 'feiticos/confirmacao.html', context)


@require_http_methods(["GET"])
def obter_horarios_disponiveis(request):
    """API para obter horários disponíveis para uma data"""
    data_str = request.GET.get('data', '')
    
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        # Verificar se é dia válido
        if data.weekday() not in [0, 1, 2, 3, 4]:  # Segunda a sexta
            return JsonResponse({'horarios': [], 'mensagem': 'Apenas segunda a sexta'})
        
        # Obter indisponibilidades específicas
        try:
            indisp = IndisponibilidadeFeitico.objects.get(data=data)
            
            # Se o dia inteiro está indisponível
            if indisp.dia_inteiro_indisponivel:
                return JsonResponse({
                    'horarios': [], 
                    'mensagem': 'Este dia está indisponível. Por favor, selecione outro dia.'
                })
            
            horas_indisponiveis = indisp.horas_indisponiveis
        except IndisponibilidadeFeitico.DoesNotExist:
            horas_indisponiveis = []
        
        # Gerar horários disponíveis
        horarios = []
        for hora in range(8, 19):
            # Verificar se está em período permitido
            if (8 <= hora < 12) or (14 <= hora < 18):
                # Verificar se não está indisponível
                if hora not in horas_indisponiveis:
                    # Verificar se já existe feitiço
                    existe = Feitico.objects.filter(
                        data_agendamento=data,
                        hora_agendamento=f'{hora:02d}:00',
                        status__in=['pago', 'realizado']
                    ).exists()
                    
                    if not existe:
                        horarios.append(f'{hora:02d}:00')
        
        return JsonResponse({'horarios': horarios})
    
    except ValueError:
        return JsonResponse({'horarios': [], 'mensagem': 'Data inválida'})


# ===== VIEWS DO PAINEL ADMINISTRATIVO CUSTOMIZADO =====

def admin_login(request):
    """Login do painel administrativo"""
    if request.user.is_authenticated:
        return redirect('admin_painel')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_painel')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'feiticos/admin/login.html')


def admin_logout(request):
    """Logout do painel administrativo"""
    logout(request)
    messages.success(request, 'Desconectado com sucesso.')
    return redirect('admin_login')


@login_required(login_url='admin_login')
def admin_painel(request):
    """Painel administrativo principal com dashboard"""
    feiticos = Feitico.objects.all()
    
    # Estatísticas
    total_feiticos = feiticos.count()
    pendentes = feiticos.filter(status='pendente').count()
    pagos = feiticos.filter(status='pago').count()
    realizados = feiticos.filter(status='realizado').count()
    
    # Renda total
    renda_total = feiticos.filter(status__in=['pago', 'realizado']).aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Próximos feitiços
    hoje = datetime.now().date()
    proximos = feiticos.filter(
        status='pago',
        data_agendamento__gte=hoje
    ).order_by('data_agendamento', 'hora_agendamento')[:5]
    
    # Dados para gráfico (últimos 30 dias)
    data_inicio = hoje - timedelta(days=30)
    feiticos_por_data = feiticos.filter(
        status__in=['pago', 'realizado'],
        data_agendamento__gte=data_inicio
    ).values('data_agendamento').annotate(
        count=Count('id'),
        renda=Sum('valor')
    ).order_by('data_agendamento')
    
    # Preparar dados para o gráfico
    datas = []
    quantidades = []
    rendas = []
    
    for item in feiticos_por_data:
        datas.append(item['data_agendamento'].strftime('%d/%m'))
        quantidades.append(item['count'])
        rendas.append(float(item['renda']))
    
    context = {
        'total_feiticos': total_feiticos,
        'pendentes': pendentes,
        'pagos': pagos,
        'realizados': realizados,
        'renda_total': f"{renda_total:.2f}",
        'proximos': proximos,
        'feiticos': feiticos,
        'datas_json': json.dumps(datas),
        'quantidades_json': json.dumps(quantidades),
        'rendas_json': json.dumps(rendas),
    }
    return render(request, 'feiticos/admin/painel.html', context)


@login_required(login_url='admin_login')
def admin_feiticos(request):
    """Listagem e edição de feitiços"""
    status_filter = request.GET.get('status', '')
    feiticos = Feitico.objects.all()
    
    if status_filter:
        feiticos = feiticos.filter(status=status_filter)
    
    context = {
        'feiticos': feiticos,
        'status_filter': status_filter,
        'status_choices': Feitico.STATUS_CHOICES,
    }
    return render(request, 'feiticos/admin/feiticos.html', context)


@login_required(login_url='admin_login')
def admin_editar_feitico(request, pk):
    """Editar feitiço"""
    feitico = get_object_or_404(Feitico, pk=pk)
    
    if request.method == 'POST':
        feitico.nome = request.POST.get('nome', feitico.nome)
        feitico.email = request.POST.get('email', feitico.email)
        feitico.telefone = request.POST.get('telefone', feitico.telefone)
        feitico.tipo_feitico = request.POST.get('tipo_feitico', feitico.tipo_feitico)
        feitico.descricao = request.POST.get('descricao', feitico.descricao)
        feitico.status = request.POST.get('status', feitico.status)
        
        try:
            data_str = request.POST.get('data_agendamento')
            hora_str = request.POST.get('hora_agendamento')
            if data_str:
                feitico.data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
            if hora_str:
                feitico.hora_agendamento = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            messages.error(request, 'Formato de data ou hora inválido.')
            return redirect('admin_editar_feitico', pk=pk)
        
        feitico.save()
        messages.success(request, 'Feitiço atualizado com sucesso.')
        return redirect('admin_feiticos')
    
    context = {
        'feitico': feitico,
        'status_choices': Feitico.STATUS_CHOICES,
    }
    return render(request, 'feiticos/admin/editar_feitico.html', context)


@login_required(login_url='admin_login')
def admin_deletar_feitico(request, pk):
    """Deletar feitiço"""
    feitico = get_object_or_404(Feitico, pk=pk)
    
    if request.method == 'POST':
        feitico.delete()
        messages.success(request, 'Feitiço deletado com sucesso.')
        return redirect('admin_feiticos')
    
    context = {'feitico': feitico}
    return render(request, 'feiticos/admin/confirmar_deletar.html', context)


@login_required(login_url='admin_login')
def admin_disponibilidade(request):
    """Gerenciar indisponibilidade de datas/horas"""
    indisponibilidades = IndisponibilidadeFeitico.objects.all().order_by('data')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'adicionar':
            data_str = request.POST.get('data')
            dia_inteiro = request.POST.get('dia_inteiro') == 'on'
            horas_str = request.POST.get('horas_indisponiveis', '').strip()
            
            try:
                data = datetime.strptime(data_str, '%Y-%m-%d').date()
                
                # Processar horas: converter "8, 9, 10" para [8, 9, 10]
                horas_list = []
                if horas_str and not dia_inteiro:
                    horas_list = [int(h.strip()) for h in horas_str.split(',') if h.strip().isdigit()]
                
                IndisponibilidadeFeitico.objects.update_or_create(
                    data=data,
                    defaults={
                        'dia_inteiro_indisponivel': dia_inteiro,
                        'horas_indisponiveis': horas_list
                    }
                )
                messages.success(request, 'Indisponibilidade atualizada com sucesso.')
            except (ValueError, IndexError):
                messages.error(request, 'Dados inválidos. Verifique o formato das horas.')
        
        elif action == 'deletar':
            indisp_id = request.POST.get('indisp_id')
            IndisponibilidadeFeitico.objects.filter(id=indisp_id).delete()
            messages.success(request, 'Indisponibilidade deletada com sucesso.')
        
        return redirect('admin_disponibilidade')
    
    context = {
        'indisponibilidades': indisponibilidades,
    }
    return render(request, 'feiticos/admin/disponibilidade.html', context)


@login_required(login_url='admin_login')
def admin_gerenciar_feiticos(request):
    """Gerenciar tipos de feitiços"""
    feiticos = TipoFeitico.objects.all().order_by('nome')
    feitico_edit = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'adicionar':
            nome = request.POST.get('nome', '').strip()
            emoji = request.POST.get('emoji', '🔮').strip()
            preco_str = request.POST.get('preco', '0').strip()
            descricao = request.POST.get('descricao', '').strip()
            ativo = request.POST.get('ativo') == 'on'
            
            try:
                preco = float(preco_str)
                TipoFeitico.objects.create(
                    nome=nome,
                    emoji=emoji,
                    preco=preco,
                    descricao=descricao,
                    ativo=ativo
                )
                messages.success(request, 'Feitiço adicionado com sucesso!')
                return redirect('admin_gerenciar_feiticos')
            except ValueError:
                messages.error(request, 'Preço inválido.')
        
        elif action == 'editar':
            feitico_id = request.POST.get('feitico_id')
            try:
                feitico = TipoFeitico.objects.get(id=feitico_id)
                nome = request.POST.get('nome', '').strip()
                emoji = request.POST.get('emoji', '🔮').strip()
                preco_str = request.POST.get('preco', '0').strip()
                descricao = request.POST.get('descricao', '').strip()
                ativo = request.POST.get('ativo') == 'on'
                
                preco = float(preco_str)
                feitico.nome = nome
                feitico.emoji = emoji
                feitico.preco = preco
                feitico.descricao = descricao
                feitico.ativo = ativo
                feitico.save()
                
                messages.success(request, 'Feitiço atualizado com sucesso!')
                return redirect('admin_gerenciar_feiticos')
            except (TipoFeitico.DoesNotExist, ValueError):
                messages.error(request, 'Erro ao atualizar feitiço.')
        
        elif action == 'deletar':
            feitico_id = request.POST.get('feitico_id')
            try:
                TipoFeitico.objects.get(id=feitico_id).delete()
                messages.success(request, 'Feitiço deletado com sucesso!')
            except TipoFeitico.DoesNotExist:
                messages.error(request, 'Feitiço não encontrado.')
            return redirect('admin_gerenciar_feiticos')
        
        elif action == 'editar_form':
            feitico_id = request.POST.get('feitico_id')
            try:
                feitico_edit = TipoFeitico.objects.get(id=feitico_id)
            except TipoFeitico.DoesNotExist:
                messages.error(request, 'Feitiço não encontrado.')
    
    context = {
        'feiticos': feiticos,
        'feitico_edit': feitico_edit,
    }
    return render(request, 'feiticos/admin/gerenciar_feiticos.html', context)
