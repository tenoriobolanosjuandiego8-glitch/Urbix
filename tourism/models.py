"""tourism/models.py"""
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from accounts.validators import validate_image_file


class TouristPlace(models.Model):
    name = models.CharField('Nombre', max_length=150)
    tag = models.CharField('Categoría', max_length=100)
    history = models.TextField('Historia', blank=True)
    curiosities = models.TextField('Curiosidades', blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    cover_image = models.ImageField(upload_to='tourism/', blank=True, null=True, validators=[validate_image_file])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    favorites = GenericRelation('interactions.Favorite')
    comments = GenericRelation('interactions.Comment')
    ratings = GenericRelation('interactions.Rating')

    class Meta:
        verbose_name = 'Lugar turístico'
        verbose_name_plural = 'Lugares turísticos'
        ordering = ['name']

    def __str__(self):
        return self.name


class TouristPlaceImage(models.Model):
    place = models.ForeignKey(TouristPlace, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='tourism/gallery/', validators=[validate_image_file])
    caption = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = 'Imagen de lugar turístico'
        verbose_name_plural = 'Galería de lugares turísticos'
