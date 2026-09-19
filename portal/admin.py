from django.contrib import admin
from .models import ShortenedURL


@admin.register(ShortenedURL)
class ShortenedURLAdmin(admin.ModelAdmin):
    list_display = ('short_code', 'destination_url', 'identifier', 'created_at')
    search_fields = ('short_code', 'destination_url')
    readonly_fields = ('identifier', 'created_at')

# Register your models here.
