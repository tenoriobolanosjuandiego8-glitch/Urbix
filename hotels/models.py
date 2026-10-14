"""hotels/models.py"""
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from accounts.validators import validate_image_file


class Hotel(models.Model):
    name = models.CharField('Nombre', max_length=150)
    description = models.TextField('Descripción', blank=True)
    address = models.CharField('Dirección', max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    approx_price = models.DecimalField('Precio aproximado (COP/noche)', max_digits=10, decimal_places=0, default=0)
    services = models.CharField('Servicios (separados por coma)', max_length=300, blank=True,
                                 help_text='Wifi, Piscina, Desayuno, Parqueadero...')
    phone = models.CharField('Teléfono', max_length=30, blank=True)
    cover_image = models.ImageField(upload_to='hotels/', blank=True, null=True, validators=[validate_image_file])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    favorites = GenericRelation('interactions.Favorite')
    comments = GenericRelation('interactions.Comment')
    ratings = GenericRelation('interactions.Rating')

    class Meta:
        verbose_name = 'Hotel'
        verbose_name_plural = 'Hoteles'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def services_list(self):
        return [s.strip() for s in self.services.split(',') if s.strip()]


class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='hotels/gallery/', validators=[validate_image_file])
    caption = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = 'Imagen de hotel'
        verbose_name_plural = 'Galería de hoteles'
