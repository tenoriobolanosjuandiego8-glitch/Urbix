"""events/models.py"""
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from accounts.validators import validate_image_file


class Event(models.Model):
    class Category(models.TextChoices):
        RELIGIOSO = 'religioso', 'Tradición religiosa'
        GASTRONOMICO = 'gastronomico', 'Gastronómico'
        MUSICAL = 'musical', 'Música en vivo'
        CULTURAL = 'cultural', 'Cultural'
        FERIA = 'feria', 'Feria'

    name = models.CharField('Nombre', max_length=150)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.CULTURAL)
    description = models.TextField('Descripción', blank=True)
    place = models.CharField('Lugar', max_length=150)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    start_at = models.DateTimeField('Fecha y hora de inicio')
    end_at = models.DateTimeField('Fecha y hora de fin', null=True, blank=True)
    cover_image = models.ImageField(upload_to='events/', blank=True, null=True, validators=[validate_image_file])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    favorites = GenericRelation('interactions.Favorite')
    comments = GenericRelation('interactions.Comment')
    ratings = GenericRelation('interactions.Rating')

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['start_at']

    def __str__(self):
        return self.name

    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.start_at >= timezone.now()


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='events/gallery/', validators=[validate_image_file])
    caption = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = 'Imagen de evento'
        verbose_name_plural = 'Galería de eventos'
