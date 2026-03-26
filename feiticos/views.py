from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Sum
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime, timedelta
import json

from .models import Agendamento, TipoFeitico, TipoTarot, IndisponibilidadeFeitico


def index(request):
    """Página inicial com dois botões"""
    return render(request, 'feiticos/index.html')


def escolher_tarot(request):
    """Página para escolher tarot"""
    if request.method == 'POST':
        return agendar_produto(request)
    
    tarots = TipoTarot.obter_tarots_disponiveis()
    context = {'produtos': tarots, 'tipo_produto': 'tarot'}
    return render(request, 'feiticos/escolher_produto.html', context)


def escolher_tarot_acompanhamento(request):
    """Página para agendar tarot de acompanhamento"""
    if request.method == 'POST':
        return agendar_produto(request)
    
    # Tarot de acompanhamento não tem subcategorias, apenas um tipo
    acompanhamento = [{
        'nome': 'Tiragem de Acompanhamento',
        'emoji': '✨',
        'preco': 50.00
    }]
    context = {'produtos': acompanhamento, 'tipo_produto': 'tarot_acompanhamento'}
    return render(request, 'feiticos/escolher_produto.html', context)


def escolher_intencao_feitico(request):
    """Página para escolher intenção de feitiço"""
    if request.method == 'POST':
        return agendar_produto(request)
    
    # Obter feitiços e criar intenções com preço fixo de 50
    feiticos = TipoFeitico.obter_feiticos_disponiveis()
    intencoes = []
    for f in feiticos:
        intencoes.append({
            'nome': f'Intenção Feitiço {f["nome"]}',
            'emoji': f['emoji'],
            'preco': 50.00,
            'original_nome': f['nome']
        })
    
    context = {'produtos': intencoes, 'tipo_produto': 'intencao_feitico'}
    return render(request, 'feiticos/escolher_produto.html', context)


def agendar_produto(request):
    """Processa o agendamento de tarot ou intenção"""
    if request.method != 'POST':
        return redirect('index')
    
    try:
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        tipo_produto = request.POST.get('tipo_produto', '').strip()
        nome_produto = request.POST.get('nome_produto', '').strip()
        data_agendamento = request.POST.get('data_agendamento', '').strip()
        valor = request.POST.get('valor', '').strip()
        
        if not all([nome, email, telefone, tipo_produto, nome_produto, data_agendamento]):
            messages.error(request, 'Por favor, preencha todos os campos.')
            return redirect('escolher_tarot' if tipo_produto == 'tarot' else 'escolher_intencao_feitico')
        
        # Se valor está vazio, usar preço padrão
        if not valor:
            if tipo_produto == 'tarot':
                valor = TipoTarot.objects.filter(nome=nome_produto).first().preco if TipoTarot.objects.filter(nome=nome_produto).exists() else 50.00
            elif tipo_produto == 'intencao_feitico':
                valor = 50.00
            else:
                valor = 99.90
        
        # Validar data
        try:
            data_obj = datetime.strptime(data_agendamento, '%Y-%m-%d').date()
            if data_obj < datetime.now().date():
                messages.error(request, 'A data não pode ser no passado.')
                return redirect('index')
        except ValueError:
            messages.error(request, 'Data inválida.')
            return redirect('index')
        
        # Verificar vagas
        disponivel, mensagem = Agendamento.verificar_vagas_disponiveis(data_obj, tipo_produto)
        if not disponivel:
            messages.error(request, mensagem)
            return redirect('index')
        
        # Converter valor para float
        try:
            preco = float(valor)
        except ValueError:
            messages.error(request, 'Valor inválido.')
            return redirect('escolher_tarot' if tipo_produto == 'tarot' else 'escolher_intencao_feitico')
        
        # Criar agendamento
        agendamento = Agendamento.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            tipo_produto=tipo_produto,
            nome_produto=nome_produto,
            data_agendamento=data_obj,
            valor=preco,
            status='pendente'
        )
        
        return redirect('pagamento', pk=agendamento.id)
    
    except Exception as e:
        messages.error(request, f'Erro ao agendar: {str(e)}')
        return redirect('index')


def pagamento(request, pk):
    """Página de pagamento"""
    try:
        agendamento = Agendamento.objects.get(id=pk)
    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
        return redirect('index')
    
    context = {
        'agendamento': agendamento,
    }
    return render(request, 'feiticos/pagamento.html', context)


def confirmar_pagamento(request, pk):
    """Confirma o pagamento (simulado)"""
    try:
        agendamento = Agendamento.objects.get(id=pk)
        agendamento.marcar_como_pago()
        
        # Se for intenção, gerar token de acesso (sem sobrescrever status)
        if agendamento.tipo_produto == 'intencao_feitico':
            agendamento.gerar_token_acesso()
        
        return redirect('confirmacao', pk=agendamento.id)
    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
        return redirect('index')


def confirmacao(request, pk):
    """Página de confirmação"""
    try:
        agendamento = Agendamento.objects.get(id=pk)
    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
        return redirect('index')
    
    context = {
        'agendamento': agendamento,
    }
    return render(request, 'feiticos/confirmacao.html', context)


def acessar_feiticos(request, token):
    """Página de acesso restrito para comprar feitiço após intenção aprovada"""
    try:
        intencao = Agendamento.objects.get(token_acesso=token, tipo_produto='intencao_feitico')
    except Agendamento.DoesNotExist:
        messages.error(request, 'Link inválido ou expirado.')
        return redirect('index')
    
    feiticos = TipoFeitico.obter_feiticos_disponiveis()
    context = {
        'intencao': intencao,
        'feiticos': feiticos,
    }
    return render(request, 'feiticos/feiticos_restrito.html', context)


def agendar_feitico(request, token):
    """Processa o agendamento de feitiço após aprovação da intenção"""
    if request.method != 'POST':
        return redirect('index')
    
    try:
        intencao = Agendamento.objects.get(
            token_acesso=token, 
            tipo_produto='intencao_feitico',
            status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado']
        )
    except Agendamento.DoesNotExist:
        messages.error(request, 'Link inválido ou expirado.')
        return redirect('index')
    
    try:
        tipo_feitico = request.POST.get('tipo_feitico', '').strip()
        data_agendamento = request.POST.get('data_agendamento', '').strip()
        
        if not all([tipo_feitico, data_agendamento]):
            messages.error(request, 'Por favor, preencha todos os campos.')
            return redirect('acessar_feiticos', token=token)
        
        # Validar data
        try:
            data_obj = datetime.strptime(data_agendamento, '%Y-%m-%d').date()
            if data_obj < datetime.now().date():
                messages.error(request, 'A data não pode ser no passado.')
                return redirect('acessar_feiticos', token=token)
        except ValueError:
            messages.error(request, 'Data inválida.')
            return redirect('acessar_feiticos', token=token)
        
        # Verificar vagas
        disponivel, mensagem = Agendamento.verificar_vagas_disponiveis(data_obj, 'feitico')
        if not disponivel:
            messages.error(request, mensagem)
            return redirect('acessar_feiticos', token=token)
        
        # Obter preço do feitiço
        preco = TipoFeitico.obter_preco(tipo_feitico)
        
        # Criar agendamento de feitiço
        agendamento = Agendamento.objects.create(
            nome=intencao.nome,
            email=intencao.email,
            telefone=intencao.telefone,
            tipo_produto='feitico',
            nome_produto=tipo_feitico,
            data_agendamento=data_obj,
            valor=preco,
            status='pendente',
            intencao_relacionada=intencao
        )
        
        return redirect('pagamento', pk=agendamento.id)
    
    except Exception as e:
        messages.error(request, f'Erro ao agendar feitiço: {str(e)}')
        return redirect('acessar_feiticos', token=token)


@require_http_methods(["GET"])
def obter_datas_disponiveis(request):
    """API para obter datas disponíveis"""
    tipo_produto = request.GET.get('tipo_produto', 'tarot')
    
    datas_disponiveis = []
    for i in range(60):
        data = datetime.now().date() + timedelta(days=i)
        
        # Verificar se há indisponibilidade marcada pelo admin
        indisponivel = IndisponibilidadeFeitico.objects.filter(data=data, indisponivel=True).exists()
        if indisponivel:
            continue
        
        # Verificar vagas disponíveis (a função já valida dias e vagas)
        tem_vaga, _ = Agendamento.verificar_vagas_disponiveis(data, tipo_produto)
        if not tem_vaga:
            continue
        
        # Se passou nas verificações, adiciona à lista
        datas_disponiveis.append(str(data))
    
    return JsonResponse({'datas': datas_disponiveis})


# ===== ADMIN VIEWS =====

def admin_login(request):
    """Login do painel administrativo"""
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
    return redirect('admin_login')


@login_required(login_url='admin_login')
def admin_painel(request):
    """Dashboard administrativo com 3 gráficos separados"""
    # Estatísticas gerais
    total_agendamentos = Agendamento.objects.count()
    
    # Contar por tipo de produto
    intencoes_count = Agendamento.objects.filter(tipo_produto='intencao_feitico', status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado', 'realizado']).count()
    tarots_count = Agendamento.objects.filter(tipo_produto='tarot', status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado', 'realizado']).count()
    feiticos_count = Agendamento.objects.filter(tipo_produto='feitico', status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado', 'realizado']).count()
    acompanhamento_count = Agendamento.objects.filter(tipo_produto='tarot_acompanhamento', status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado', 'realizado']).count()
    
    # Renda por tipo
    renda_intencao = Agendamento.objects.filter(
        tipo_produto='intencao_feitico',
        status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado', 'realizado']
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    renda_tarot = Agendamento.objects.filter(
        tipo_produto='tarot',
        status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado', 'realizado']
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    renda_feitico = Agendamento.objects.filter(
        tipo_produto='feitico',
        status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado', 'realizado']
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    renda_acompanhamento = Agendamento.objects.filter(
        tipo_produto='tarot_acompanhamento',
        status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado', 'realizado']
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    renda_total = float(renda_intencao) + float(renda_tarot) + float(renda_feitico) + float(renda_acompanhamento)
    
    # Próximos agendamentos
    proximos = Agendamento.objects.filter(
        status__in=['pagamento_confirmado', 'pago'],
        data_agendamento__gte=datetime.now().date()
    ).order_by('data_agendamento')[:10]
    
    # Dados para gráficos - Range: hoje-7 até último agendamento, sem buracos
    data_minima = datetime.now().date() - timedelta(days=7)
    
    # Buscar todos os agendamentos com status válido
    agendamentos_para_grafico = Agendamento.objects.filter(
        status__in=['pagamento_confirmado', 'enviar_link', 'link_enviado', 'realizado']
    ).order_by('data_agendamento')
    
    # Determinar data máxima
    if agendamentos_para_grafico.exists():
        data_maxima = agendamentos_para_grafico.last().data_agendamento
        # Se a data máxima for menor que hoje-7, usar hoje
        if data_maxima < data_minima:
            data_maxima = datetime.now().date()
    else:
        data_maxima = datetime.now().date()
    
    # Criar dicionários para cada tipo de produto
    datas_dict_intencao = {}
    datas_dict_tarot = {}
    datas_dict_feitico = {}
    datas_dict_acompanhamento = {}
    
    # Preencher dicionários com todas as datas no range (sem buracos)
    data_atual = data_minima
    while data_atual <= data_maxima:
        datas_dict_intencao[data_atual] = {'quantidade': 0, 'renda': 0}
        datas_dict_tarot[data_atual] = {'quantidade': 0, 'renda': 0}
        datas_dict_feitico[data_atual] = {'quantidade': 0, 'renda': 0}
        datas_dict_acompanhamento[data_atual] = {'quantidade': 0, 'renda': 0}
        data_atual += timedelta(days=1)
    
    # Preencher dados dos agendamentos
    for ag in agendamentos_para_grafico:
        if ag.tipo_produto == 'intencao_feitico' and ag.data_agendamento in datas_dict_intencao:
            datas_dict_intencao[ag.data_agendamento]['quantidade'] += 1
            datas_dict_intencao[ag.data_agendamento]['renda'] += float(ag.valor)
        elif ag.tipo_produto == 'tarot' and ag.data_agendamento in datas_dict_tarot:
            datas_dict_tarot[ag.data_agendamento]['quantidade'] += 1
            datas_dict_tarot[ag.data_agendamento]['renda'] += float(ag.valor)
        elif ag.tipo_produto == 'feitico' and ag.data_agendamento in datas_dict_feitico:
            datas_dict_feitico[ag.data_agendamento]['quantidade'] += 1
            datas_dict_feitico[ag.data_agendamento]['renda'] += float(ag.valor)
        elif ag.tipo_produto == 'tarot_acompanhamento' and ag.data_agendamento in datas_dict_acompanhamento:
            datas_dict_acompanhamento[ag.data_agendamento]['quantidade'] += 1
            datas_dict_acompanhamento[ag.data_agendamento]['renda'] += float(ag.valor)
    
    # Gerar dados para o range de datas (sem buracos)
    datas_lista = []
    intencao_qtd = []
    intencao_renda = []
    tarot_qtd = []
    tarot_renda = []
    feitico_qtd = []
    feitico_renda = []
    acompanhamento_qtd = []
    acompanhamento_renda = []
    
    data_atual = data_minima
    while data_atual <= data_maxima:
        datas_lista.append(data_atual.strftime('%d/%m'))
        
        intencao_qtd.append(datas_dict_intencao.get(data_atual, {}).get('quantidade', 0))
        intencao_renda.append(float(datas_dict_intencao.get(data_atual, {}).get('renda', 0)))
        
        tarot_qtd.append(datas_dict_tarot.get(data_atual, {}).get('quantidade', 0))
        tarot_renda.append(float(datas_dict_tarot.get(data_atual, {}).get('renda', 0)))
        
        feitico_qtd.append(datas_dict_feitico.get(data_atual, {}).get('quantidade', 0))
        feitico_renda.append(float(datas_dict_feitico.get(data_atual, {}).get('renda', 0)))
        
        acompanhamento_qtd.append(datas_dict_acompanhamento.get(data_atual, {}).get('quantidade', 0))
        acompanhamento_renda.append(float(datas_dict_acompanhamento.get(data_atual, {}).get('renda', 0)))
        
        data_atual += timedelta(days=1)
    
    datas_json = json.dumps(datas_lista)
    intencao_qtd_json = json.dumps(intencao_qtd)
    intencao_renda_json = json.dumps(intencao_renda)
    tarot_qtd_json = json.dumps(tarot_qtd)
    tarot_renda_json = json.dumps(tarot_renda)
    feitico_qtd_json = json.dumps(feitico_qtd)
    feitico_renda_json = json.dumps(feitico_renda)
    acompanhamento_qtd_json = json.dumps(acompanhamento_qtd)
    acompanhamento_renda_json = json.dumps(acompanhamento_renda)
    
    context = {
        'total_agendamentos': total_agendamentos,
        'intencoes_count': intencoes_count,
        'tarots_count': tarots_count,
        'feiticos_count': feiticos_count,
        'acompanhamento_count': acompanhamento_count,
        'renda_intencao': f"{renda_intencao:.2f}",
        'renda_tarot': f"{renda_tarot:.2f}",
        'renda_feitico': f"{renda_feitico:.2f}",
        'renda_acompanhamento': f"{renda_acompanhamento:.2f}",
        'renda_total': f"{renda_total:.2f}",
        'proximos': proximos,
        'datas_json': datas_json,
        'intencao_qtd_json': intencao_qtd_json,
        'intencao_renda_json': intencao_renda_json,
        'tarot_qtd_json': tarot_qtd_json,
        'tarot_renda_json': tarot_renda_json,
        'feitico_qtd_json': feitico_qtd_json,
        'feitico_renda_json': feitico_renda_json,
        'acompanhamento_qtd_json': acompanhamento_qtd_json,
        'acompanhamento_renda_json': acompanhamento_renda_json,
    }
    
    return render(request, 'feiticos/admin/painel.html', context)


@login_required(login_url='admin_login')
def admin_agendamentos(request):
    """Listagem de agendamentos"""
    status_filter = request.GET.get('status')
    tipo_filter = request.GET.get('tipo')
    
    agendamentos = Agendamento.objects.all().order_by('-criado_em')
    
    if status_filter:
        agendamentos = agendamentos.filter(status=status_filter)
    
    if tipo_filter:
        agendamentos = agendamentos.filter(tipo_produto=tipo_filter)
    
    status_choices = Agendamento.STATUS_CHOICES
    tipo_choices = Agendamento.TIPO_PRODUTO_CHOICES
    
    context = {
        'agendamentos': agendamentos,
        'status_choices': status_choices,
        'tipo_choices': tipo_choices,
        'status_filter': status_filter,
        'tipo_filter': tipo_filter,
    }
    
    return render(request, 'feiticos/admin/agendamentos.html', context)


@login_required(login_url='admin_login')
def admin_editar_agendamento(request, pk):
    """Editar agendamento"""
    try:
        agendamento = Agendamento.objects.get(id=pk)
    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
        return redirect('admin_agendamentos')
    
    if request.method == 'POST':
        novo_status = request.POST.get('status')
        if novo_status:
            agendamento.status = novo_status
            agendamento.save()
            messages.success(request, 'Agendamento atualizado com sucesso!')
            return redirect('admin_agendamentos')
    
    status_choices = Agendamento.STATUS_CHOICES
    
    context = {
        'agendamento': agendamento,
        'status_choices': status_choices,
    }
    
    return render(request, 'feiticos/admin/editar_agendamento.html', context)


@login_required(login_url='admin_login')
def admin_indisponibilidade(request):
    """Gerenciar indisponibilidade"""
    if request.method == 'POST':
        data_str = request.POST.get('data')
        
        if data_str:
            try:
                data = datetime.strptime(data_str, '%Y-%m-%d').date()
                
                # Verificar se já existe
                indisp, created = IndisponibilidadeFeitico.objects.get_or_create(data=data)
                if created:
                    indisp.indisponivel = True
                    indisp.save()
                    messages.success(request, 'Data marcada como indisponível!')
                else:
                    # Toggle: se já existe, inverte o status
                    indisp.indisponivel = not indisp.indisponivel
                    indisp.save()
                    status = 'indisponível' if indisp.indisponivel else 'disponível'
                    messages.success(request, f'Data marcada como {status}!')
            except ValueError:
                messages.error(request, 'Data inválida.')
    
    indisponibilidades = IndisponibilidadeFeitico.objects.all().order_by('-data')
    
    context = {
        'indisponibilidades': indisponibilidades,
    }
    
    return render(request, 'feiticos/admin/indisponibilidade.html', context)


@login_required(login_url='admin_login')
def admin_gerenciar_produtos(request):
    """Gerenciar feitiços e tarots"""
    feiticos = TipoFeitico.objects.all()
    tarots = TipoTarot.objects.all()
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        tipo = request.POST.get('tipo')
        
        if acao == 'adicionar':
            nome = request.POST.get('nome')
            emoji = request.POST.get('emoji', '🔮')
            preco = request.POST.get('preco')
            descricao = request.POST.get('descricao', '')
            
            if tipo == 'feitico':
                TipoFeitico.objects.create(
                    nome=nome,
                    emoji=emoji,
                    preco=float(preco),
                    descricao=descricao
                )
                messages.success(request, 'Feitiço adicionado!')
            else:
                TipoTarot.objects.create(
                    nome=nome,
                    emoji=emoji,
                    preco=float(preco),
                    descricao=descricao
                )
                messages.success(request, 'Tarot adicionado!')
        
        elif acao == 'editar':
            produto_id = request.POST.get('produto_id')
            nome = request.POST.get('nome')
            emoji = request.POST.get('emoji', '🔮')
            preco = request.POST.get('preco')
            descricao = request.POST.get('descricao', '')
            
            if tipo == 'feitico':
                produto = TipoFeitico.objects.get(id=produto_id)
                produto.nome = nome
                produto.emoji = emoji
                produto.preco = float(preco)
                produto.descricao = descricao
                produto.save()
                messages.success(request, 'Feitiço atualizado!')
            else:
                produto = TipoTarot.objects.get(id=produto_id)
                produto.nome = nome
                produto.emoji = emoji
                produto.preco = float(preco)
                produto.descricao = descricao
                produto.save()
                messages.success(request, 'Tarot atualizado!')
        
        elif acao == 'deletar':
            produto_id = request.POST.get('produto_id')
            
            if tipo == 'feitico':
                TipoFeitico.objects.filter(id=produto_id).delete()
                messages.success(request, 'Feitiço deletado!')
            else:
                TipoTarot.objects.filter(id=produto_id).delete()
                messages.success(request, 'Tarot deletado!')
        
        return redirect('admin_gerenciar_produtos')
    
    context = {
        'feiticos': feiticos,
        'tarots': tarots,
    }
    
    return render(request, 'feiticos/admin/gerenciar_produtos.html', context)
