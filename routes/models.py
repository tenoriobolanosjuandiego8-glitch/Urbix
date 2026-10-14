"""
routes/models.py
Operadores de transporte (empresas reales de Popayán), rutas,
paraderos/lugares de interés y horarios de paso.
"""
import uuid

from django.db import models


class Operator(models.Model):
    """Empresa de transporte urbano real de Popayán."""
    name = models.CharField('Nombre', max_length=80, unique=True)
    brand_color = models.CharField('Color de marca (hex)', max_length=7, default='#4CFF6E')
    phone = models.CharField('Teléfono', max_length=30, blank=True)
    website = models.URLField('Sitio web', blank=True)
    fleet_size = models.PositiveIntegerField('Tamaño de flota (aprox., informativo)', default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Operador de transporte'
        verbose_name_plural = 'Operadores de transporte'
        ordering = ['name']

    def __str__(self):
        return self.name


class Stop(models.Model):
    """Paradero, barrio, universidad, hospital, parque o lugar de referencia."""

    class Category(models.TextChoices):
        PARADERO = 'paradero', 'Paradero'
        BARRIO = 'barrio', 'Barrio / sector'
        TERMINAL = 'terminal', 'Terminal de transporte'
        UNIVERSIDAD = 'universidad', 'Universidad / colegio'
        HOSPITAL = 'hospital', 'Hospital / centro de salud'
        PARQUE = 'parque', 'Parque'
        CENTRO_COMERCIAL = 'centro_comercial', 'Centro comercial'
        REFERENCIA = 'referencia', 'Punto de referencia'

    name = models.CharField('Nombre', max_length=120)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.BARRIO)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField('Dirección', max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Paradero / Lugar'
        verbose_name_plural = 'Paraderos y lugares'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def routes_here(self):
        return Route.objects.filter(stops=self, is_active=True).distinct()


class Route(models.Model):
    """Ruta de transporte urbano, operada por una empresa real."""
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True, related_name='routes')
    code = models.CharField('Código (ej. TP1BT)', max_length=20, blank=True)
    name = models.CharField('Nombre', max_length=80)            # ej. "Ruta 1"
    origin = models.CharField('Origen', max_length=120)
    destination = models.CharField('Destino', max_length=120)
    description = models.CharField('Descripción', max_length=200, blank=True)
    color = models.CharField('Color (hex)', max_length=7, default='#4CFF6E')
    duration_minutes = models.PositiveIntegerField('Duración estimada (min)', default=30)
    distance_km = models.DecimalField('Distancia (km)', max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField('Activa', default=True)
    stops = models.ManyToManyField(Stop, through='RouteStop', related_name='routes')
    # Ruta real siguiendo calles (GeoJSON de coordenadas), calculada opcionalmente
    # con OpenRouteService. Si está vacía, el mapa dibuja líneas rectas entre paraderos.
    snapped_path = models.JSONField('Recorrido real (calculado)', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'
        ordering = ['operator__name', 'name']

    def __str__(self):
        empresa = f'{self.operator.name} · ' if self.operator else ''
        return f'{empresa}{self.name}: {self.origin} - {self.destination}'

    @property
    def path_coordinates(self):
        """
        Lista [ [lat,lng], ... ] para dibujar en Leaflet.
        Usa el recorrido real (snapped_path) si ya fue calculado con
        OpenRouteService; si no, conecta los paraderos con líneas rectas.
        """
        if self.snapped_path:
            return self.snapped_path
        return [[rs.stop.latitude, rs.stop.longitude] for rs in self.routestop_set.select_related('stop').order_by('order')]

    @property
    def stops_summary(self):
        return ' → '.join(rs.stop.name for rs in self.routestop_set.select_related('stop').order_by('order'))


class RouteStop(models.Model):
    """Tabla intermedia: orden de los paraderos dentro de una ruta."""
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Paradero de ruta'
        verbose_name_plural = 'Paraderos de ruta'
        ordering = ['route', 'order']
        unique_together = ('route', 'stop', 'order')

    def __str__(self):
        return f'{self.route.name} · #{self.order} {self.stop.name}'


class TripShare(models.Model):
    """
    Enlace temporal para compartir un viaje (ruta + posición aproximada)
    con un contacto de confianza, sin que necesite cuenta en URBIX.
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='trip_shares')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True)
    origin_stop = models.ForeignKey(Stop, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    destination_stop = models.ForeignKey(Stop, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Viaje compartido'
        verbose_name_plural = 'Viajes compartidos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} comparte viaje · {self.token}'

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class ScheduleEntry(models.Model):
    """Horario de salida y frecuencia estimada para una ruta."""
    class Day(models.TextChoices):
        HABIL = 'habil', 'Día hábil'
        SABADO = 'sabado', 'Sábado'
        FESTIVO = 'festivo', 'Domingo y festivos'

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedule_entries')
    day_type = models.CharField(max_length=10, choices=Day.choices, default=Day.HABIL)
    departure_time = models.TimeField('Hora de salida')
    frequency_minutes = models.PositiveIntegerField('Frecuencia (min)', default=15)

    class Meta:
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'
        ordering = ['route', 'day_type', 'departure_time']

    def __str__(self):
        return f'{self.route.name} · {self.get_day_type_display()} · {self.departure_time}'
