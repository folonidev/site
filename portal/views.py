from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from urllib.parse import urlparse

from .models import ShortenedURL


def normalize_destination_url(value):
    """Adiciona HTTPS para tornar o protocolo opcional no formulário."""
    if value.startswith('//'):
        return f'https:{value}'
    if '://' not in value:
        return f'https://{value}'
    return value


def home(request):
    return render(request, 'index.html')


def shortener(request):
    context = {}
    if request.method == 'POST':
        destination_url = normalize_destination_url(
            request.POST.get('destination_url', '').strip()
        )
        short_code = request.POST.get('short_code', '').strip()
        link = ShortenedURL(short_code=short_code, destination_url=destination_url)

        try:
            link.full_clean()
        except ValidationError as error:
            context['errors'] = error.message_dict
            context['destination_url'] = destination_url
            context['short_code'] = short_code
        else:
            link.save()
            short_url = request.build_absolute_uri(
                reverse('follow_short_url', kwargs={'short_code': link.short_code})
            )
            return render(request, 'shortener.html', {'short_url': short_url})

    return render(request, 'shortener.html', context)


def follow_short_url(request, short_code):
    link = get_object_or_404(ShortenedURL, short_code=short_code)
    # A validação de URLField impede URLs malformadas. Esta proteção adicional
    # restringe dados legados a destinos HTTP(S).
    parsed_url = urlparse(link.destination_url)
    if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
        raise Http404('Destino inválido.')
    return redirect(link.destination_url)

def blog(request):
    return render(request, 'blog.html')

def portfolio(request):
    return render(request, 'portfolio.html')
