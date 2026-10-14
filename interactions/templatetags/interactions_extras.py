"""
interactions/templatetags/interactions_extras.py
Filtros de plantilla para consultar favoritos, calificación promedio
y comentarios de cualquier objeto desde los templates.
"""
from django import template
from django.contrib.contenttypes.models import ContentType
from ..models import Favorite, Comment, average_rating

register = template.Library()


@register.filter
def is_favorite(user, obj):
    if not user.is_authenticated:
        return False
    ct = ContentType.objects.get_for_model(obj)
    return Favorite.objects.filter(user=user, content_type=ct, object_id=obj.pk).exists()


@register.filter
def avg_rating(obj):
    return average_rating(obj)


@register.filter
def comments_for(obj):
    ct = ContentType.objects.get_for_model(obj)
    return Comment.objects.filter(content_type=ct, object_id=obj.pk, parent__isnull=True).select_related('user')


@register.simple_tag
def content_type_of(obj):
    ct = ContentType.objects.get_for_model(obj)
    return f'{ct.app_label}/{ct.model}'


@register.filter
def get_item(d, key):
    """Permite hacer diccionario|get_item:llave en templates."""
    if not d:
        return None
    return d.get(key)
