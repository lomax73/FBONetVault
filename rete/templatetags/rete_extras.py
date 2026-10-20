from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..icone import ICONE, chiave_icona

register = template.Library()


@register.simple_tag
def icona_tipo(nome_tipo, size=16):
    """SVG inline dell'icona per un tipo di apparato (vedi rete/icone.py)."""
    return format_html(
        '<svg viewBox="0 0 24 24" width="{0}" height="{0}" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{1}</svg>',
        size, mark_safe(ICONE[chiave_icona(nome_tipo)]),  # markup costante di rete/icone.py, non input utente
    )
