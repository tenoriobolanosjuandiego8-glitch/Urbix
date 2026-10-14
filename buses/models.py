"""
buses/models.py
Vehículos (buses) de la flota URBIX.
"""
from django.db import models
from routes.models import Route


class Bus(models.Model):
    class Status(models.TextChoices):
        EN_RUTA = 'en_ruta', 'En ruta'
        RETRASO = 'retraso', 'Con retraso'
        MANTENIMIENTO = 'mantenimiento', 'En mantenimiento'
        FUERA_SERVICIO = 'fuera_servicio', 'Fuera de servicio'

    class Occupancy(models.TextChoices):
        BAJA = 'baja', 'Poco ocupado'
        MEDIA = 'media', 'Ocupación media'
        ALTA = 'alta', 'Casi lleno'
        LLENO = 'lleno', 'Lleno'

    code = models.CharField('Código', max_length=20, unique=True)   # ej. BUS-104
    plate = models.CharField('Placa', max_length=10, unique=True)
    capacity = models.PositiveIntegerField('Capacidad', default=30)
    occupancy = models.CharField('Ocupación (simulada)', max_length=10, choices=Occupancy.choices, default=Occupancy.MEDIA)
    model_year = models.PositiveIntegerField('Modelo (año)', null=True, blank=True)
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='buses')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.EN_RUTA)
    last_speed_kmh = models.FloatField('Última velocidad (km/h)', default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'
        ordering = ['code']

    @property
    def operator(self):
        return self.route.operator if self.route and self.route.operator else None

    @property
    def operator_name(self):
        return self.operator.name if self.operator else 'Sin asignar'

    def __str__(self):
        return self.code

    @property
    def current_driver(self):
        return self.drivers.filter(status='activo').first()

    @property
    def last_position(self):
        return self.gps_locations.order_by('-recorded_at').first()
