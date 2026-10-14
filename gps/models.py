"""
gps/models.py
Registro de ubicaciones GPS de los buses. Preparado para recibir datos
reales (vía API) y también para simular movimiento mientras tanto.
"""
from django.db import models
from buses.models import Bus
from accounts.models import User


class GPSLocation(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='gps_locations')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='gps_reports')
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed_kmh = models.FloatField(default=0)
    heading = models.FloatField('Rumbo (grados)', default=0, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ubicación GPS'
        verbose_name_plural = 'Ubicaciones GPS'
        ordering = ['-recorded_at']
        indexes = [models.Index(fields=['bus', '-recorded_at'])]

    def __str__(self):
        return f'{self.bus.code} @ ({self.latitude:.5f}, {self.longitude:.5f}) · {self.recorded_at:%H:%M:%S}'
