"""
interactions/models.py
Modelos genéricos reutilizados por restaurantes, hoteles, lugares
turísticos, eventos y rutas: Favoritos, Comentarios, Calificaciones
e Historial de navegación del usuario.

Se usan GenericForeignKey para no repetir "favorito_restaurante",
"favorito_hotel", etc. por cada tipo de contenido.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} ♥ {self.content_object}'


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    body = models.TextField('Comentario', max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user}: {self.body[:40]}'


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    score = models.PositiveSmallIntegerField('Calificación (1-5)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        unique_together = ('user', 'content_type', 'object_id')

    def __str__(self):
        return f'{self.user} → {self.score}★ {self.content_object}'


class HistoryEntry(models.Model):
    """Historial de navegación: rutas consultadas, lugares visitados, etc."""
    class Kind(models.TextChoices):
        VIEW = 'view', 'Visualización'
        SEARCH = 'search', 'Búsqueda'
        FAVORITE = 'favorite', 'Favorito'
        COMMENT = 'comment', 'Comentario'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='history')
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.VIEW)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    detail = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial'
        verbose_name_plural = 'Historial'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} · {self.get_kind_display()} · {self.created_at:%Y-%m-%d %H:%M}'


def toggle_favorite(user, obj):
    """Agrega o quita de favoritos; retorna True si quedó agregado."""
    ct = ContentType.objects.get_for_model(obj)
    fav, created = Favorite.objects.get_or_create(user=user, content_type=ct, object_id=obj.pk)
    if not created:
        fav.delete()
        return False
    HistoryEntry.objects.create(user=user, kind=HistoryEntry.Kind.FAVORITE, content_type=ct, object_id=obj.pk)
    return True


class ContentFlag(models.Model):
    """Permite a un usuario denunciar un comentario/reseña inapropiado."""
    class Reason(models.TextChoices):
        SPAM = 'spam', 'Spam o publicidad'
        OFENSIVO = 'ofensivo', 'Lenguaje ofensivo'
        FALSO = 'falso', 'Información falsa'
        OTRO = 'otro', 'Otro motivo'

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='flags')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='content_flags')
    reason = models.CharField(max_length=10, choices=Reason.choices, default=Reason.OTRO)
    note = models.CharField(max_length=300, blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Denuncia de contenido'
        verbose_name_plural = 'Denuncias de contenido'
        ordering = ['-created_at']
        unique_together = ('comment', 'reported_by')

    def __str__(self):
        return f'Denuncia de {self.reported_by} sobre comentario #{self.comment_id}'


def average_rating(obj):
    ct = ContentType.objects.get_for_model(obj)
    agg = Rating.objects.filter(content_type=ct, object_id=obj.pk).aggregate(models.Avg('score'))
    return round(agg['score__avg'] or 0, 1)


def get_recommendations_for_user(user, limit=6):
    """
    Recomendaciones simples basadas en reglas: mira las categorías (tag)
    de los restaurantes/lugares que el usuario ya marcó como favoritos,
    y el tipo de negocios que ha visto en su historial, y sugiere otros
    de esas mismas categorías mejor calificados que no haya guardado
    todavía. No usa IA — es rápido, gratis y predecible.
    """
    from restaurants.models import Restaurant
    from tourism.models import TouristPlace

    if not user.is_authenticated:
        return []

    favorites = Favorite.objects.filter(user=user).select_related('content_type')
    favorite_ids_by_model = {}
    liked_tags = set()
    liked_business_types = set()

    for fav in favorites:
        model = fav.content_type.model
        favorite_ids_by_model.setdefault(model, set()).add(fav.object_id)
        obj = fav.content_object
        tag = getattr(obj, 'tag', None)
        if tag:
            liked_tags.add(tag)
        business_type = getattr(obj, 'business_type', None)
        if business_type:
            liked_business_types.add(business_type)

    # También miramos qué tipos de negocio ha visitado en su historial reciente
    recent_business_ct = ContentType.objects.filter(app_label='business', model='business').first()
    if recent_business_ct:
        recent_views = HistoryEntry.objects.filter(
            user=user, content_type=recent_business_ct
        ).select_related('content_type')[:20]
        for entry in recent_views:
            obj = entry.content_object
            if obj is not None:
                liked_business_types.add(obj.business_type)

    recommendations = []
    if liked_tags:
        for Model, model_name in [(Restaurant, 'restaurant'), (TouristPlace, 'touristplace')]:
            excluded = favorite_ids_by_model.get(model_name, set())
            qs = Model.objects.filter(is_active=True, tag__in=liked_tags).exclude(pk__in=excluded)
            recommendations.extend(qs[:limit])

    if liked_business_types and len(recommendations) < limit:
        from business.models import Business
        excluded_businesses = favorite_ids_by_model.get('business', set())
        biz_qs = (Business.objects.filter(status=Business.Status.APROBADO, business_type__in=liked_business_types)
                  .exclude(pk__in=excluded_businesses).order_by('-plan', '-created_at'))
        recommendations.extend(biz_qs[:limit - len(recommendations)])

    return recommendations[:limit]
