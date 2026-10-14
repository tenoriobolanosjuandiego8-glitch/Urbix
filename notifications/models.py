"""
notifications/models.py
Sistema de notificaciones: bus cercano, cambios de ruta, eventos,
incidentes y noticias. Preparado para integrarse con push/WebSockets
más adelante (el campo `channel` documenta el canal previsto).
"""
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Notification(models.Model):
    class Kind(models.TextChoices):
        BUS_CERCANO = 'bus_cercano', 'Bus cercano'
        CAMBIO_RUTA = 'cambio_ruta', 'Cambio de ruta'
        EVENTO = 'evento', 'Evento'
        INCIDENTE = 'incidente', 'Incidente'
        NOTICIA = 'noticia', 'Noticia'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.NOTICIA)
    title = models.CharField(max_length=150)
    body = models.CharField(max_length=300, blank=True)
    icon = models.CharField(max_length=40, default='bi-bell')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} · {self.title}'


class PushSubscription(models.Model):
    """Suscripción del navegador de un usuario a notificaciones push
    (Web Push API). Un usuario puede tener varias si usa la app desde
    distintos dispositivos/navegadores."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscripción push'
        verbose_name_plural = 'Suscripciones push'

    def __str__(self):
        return f'{self.user} · {self.endpoint[:40]}...'


class Alerta(models.Model):
    TIPO = (
        ('llegada_bus', 'Llegada del bus'),
        ('congestión', 'Congestión reportada'),
        ('cierre_ruta', 'Cierre de ruta'),
        ('retraso', 'Retraso detectado'),
    )
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alertas')
    parada = models.ForeignKey('routes.Stop', on_delete=models.CASCADE)
    ruta = models.ForeignKey('routes.Route', on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO)
    activa = models.BooleanField(default=True)
    creada = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Alerta de usuario'
        unique_together = ('usuario', 'parada', 'ruta', 'tipo')
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} en {self.parada.name}"
