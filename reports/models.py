"""
reports/models.py
Reportes de novedades enviados por conductores (tráfico, daños
mecánicos, incidentes) y su seguimiento administrativo.
"""
from django.conf import settings
from django.db import models
from buses.models import Bus
from routes.models import Route


class Report(models.Model):
    class Kind(models.TextChoices):
        TRAFICO = 'trafico', 'Tráfico'
        MECANICO = 'mecanico', 'Daño mecánico'
        ACCIDENTE = 'accidente', 'Accidente'
        SEGURIDAD = 'seguridad', 'Seguridad'
        CIERRE_VIA = 'cierre_via', 'Cierre de vía'
        BUS_LLENO = 'bus_lleno', 'Bus lleno'
        OBJETO_PERDIDO = 'objeto_perdido', 'Objeto perdido'
        OTRO = 'otro', 'Otro'

    class Status(models.TextChoices):
        ABIERTO = 'abierto', 'Abierto'
        EN_PROCESO = 'en_proceso', 'En proceso'
        RESUELTO = 'resuelto', 'Resuelto'

    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, blank=True)
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTRO)
    description = models.TextField('Descripción')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABIERTO)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_kind_display()} · {self.driver} · {self.created_at:%Y-%m-%d %H:%M}'


class DriverShift(models.Model):
    """Vueltas / turnos realizados por un conductor en un día."""
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shifts')
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True)
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True)
    lap_number = models.PositiveIntegerField('Número de vuelta')
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    on_time = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Vuelta de conductor'
        verbose_name_plural = 'Vueltas de conductores'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.driver} · vuelta {self.lap_number}'


class ReporteTrafico(models.Model):
    NIVEL = (
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('caótico', 'Caótico'),
    )
    TIPO = (
        ('congestión', 'Congestión'),
        ('accidente', 'Accidente'),
        ('evento', 'Evento/Cierre'),
        ('otro', 'Otro'),
    )
    
    conductor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reportes_trafico')
    bus = models.ForeignKey('buses.Bus', on_delete=models.CASCADE)
    ubicacion_lat = models.FloatField()
    ubicacion_lng = models.FloatField()
    nivel = models.CharField(max_length=10, choices=NIVEL)
    tipo = models.CharField(max_length=15, choices=TIPO)
    descripcion = models.TextField(blank=True)
    creada = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)
    expira = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Reporte de tráfico'
        ordering = ['-creada']
    
    def __str__(self):
        return f"{self.get_nivel_display()} - {self.get_tipo_display()} ({self.conductor.username})"
    
    def save(self, *args, **kwargs):
        if not self.expira:
            from django.utils import timezone
            from datetime import timedelta
            self.expira = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)
