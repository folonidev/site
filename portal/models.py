from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from uuid import uuid4
from urllib.parse import urlparse


short_code_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9_-]{3,64}$',
    message='Use de 3 a 64 caracteres: letras, números, hífen ou sublinhado.',
)


class ShortenedURL(models.Model):
    """Um link criado no encurtador público."""

    identifier = models.UUIDField(default=uuid4, unique=True, editable=False)
    short_code = models.CharField(
        'atalho', max_length=64, unique=True, validators=[short_code_validator]
    )
    destination_url = models.URLField(
        'URL de destino',
        max_length=2048,
        error_messages={
            'invalid': 'Digite um endereço válido, como google.com ou https://google.com.'
        },
    )
    created_at = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'link encurtado'
        verbose_name_plural = 'links encurtados'

    def __str__(self):
        return f'{self.short_code} → {self.destination_url}'

    def clean(self):
        super().clean()
        parsed_url = urlparse(self.destination_url)
        if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
            raise ValidationError({
                'destination_url': 'Informe uma URL HTTP ou HTTPS válida.'
            })


class ShortenerQuota(models.Model):
    """Linha única usada para serializar a criação de links públicos."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)

    class Meta:
        verbose_name = 'trava do encurtador'
        verbose_name_plural = 'trava do encurtador'
