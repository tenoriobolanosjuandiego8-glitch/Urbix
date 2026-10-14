"""restaurants/models.py"""
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from accounts.validators import validate_image_file


class Restaurant(models.Model):
    name = models.CharField('Nombre', max_length=150)
    tag = models.CharField('Categoría', max_length=80)          # ej. "Gastronomía típica"
    description = models.TextField('Descripción', blank=True)
    address = models.CharField('Dirección', max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    price_range = models.CharField('Rango de precio', max_length=3, default='$$', help_text='$, $$ o $$$')
    phone = models.CharField('Teléfono', max_length=30, blank=True)
    opening_hours = models.CharField('Horario', max_length=120, blank=True, default='11:00 a.m. – 9:00 p.m.')
    cover_image = models.ImageField(upload_to='restaurants/', blank=True, null=True, validators=[validate_image_file])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    favorites = GenericRelation('interactions.Favorite')
    comments = GenericRelation('interactions.Comment')
    ratings = GenericRelation('interactions.Rating')

    class Meta:
        verbose_name = 'Restaurante'
        verbose_name_plural = 'Restaurantes'
        ordering = ['name']

    def __str__(self):
        return self.name


class RestaurantImage(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='restaurants/gallery/', validators=[validate_image_file])
    caption = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = 'Imagen de restaurante'
        verbose_name_plural = 'Galería de restaurantes'
