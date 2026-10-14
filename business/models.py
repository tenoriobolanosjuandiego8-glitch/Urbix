"""
business/models.py
Centro Empresarial URBIX: negocios locales que se registran, pasan por
verificación de un administrador, y pueden contratar planes de mayor
visibilidad (Destacado / Premium). Incluye estadísticas básicas y una
estructura lista para conectar pasarelas de pago reales más adelante.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from accounts.validators import validate_image_file
from django.utils import timezone


class Business(models.Model):
    class BusinessType(models.TextChoices):
        RESTAURANTE = 'restaurante', 'Restaurante'
        HOTEL = 'hotel', 'Hotel'
        CAFETERIA = 'cafeteria', 'Cafetería'
        BAR = 'bar', 'Bar'
        SUPERMERCADO = 'supermercado', 'Supermercado'
        DROGUERIA = 'drogueria', 'Droguería'
        CLINICA = 'clinica', 'Clínica / centro de salud'
        GIMNASIO = 'gimnasio', 'Gimnasio'
        TIENDA = 'tienda', 'Tienda'
        CENTRO_COMERCIAL = 'centro_comercial', 'Centro comercial'
        AGENCIA_VIAJES = 'agencia_viajes', 'Agencia de viajes'
        OTRO = 'otro', 'Otro negocio local'

    class Status(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente de verificación'
        APROBADO = 'aprobado', 'Aprobado'
        RECHAZADO = 'rechazado', 'Rechazado'
        SUSPENDIDO = 'suspendido', 'Suspendido'

    class Plan(models.TextChoices):
        GRATUITO = 'gratuito', 'Gratuito'
        DESTACADO = 'destacado', 'Destacado'
        PREMIUM = 'premium', 'Premium'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='businesses')
    name = models.CharField('Nombre del negocio', max_length=150)
    business_type = models.CharField('Tipo de negocio', max_length=30, choices=BusinessType.choices)
    description = models.TextField('Descripción', blank=True)
    address = models.CharField('Dirección', max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    phone = models.CharField('Teléfono', max_length=30, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=30, blank=True)
    website = models.URLField('Sitio web', blank=True)
    instagram = models.CharField('Instagram (usuario)', max_length=80, blank=True)
    facebook = models.CharField('Facebook (página)', max_length=120, blank=True)
    opening_hours = models.CharField('Horario', max_length=150, blank=True)
    cover_image = models.ImageField('Foto de portada', upload_to='business/covers/', blank=True, null=True, validators=[validate_image_file])

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDIENTE)
    rejection_reason = models.CharField('Motivo de rechazo', max_length=300, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='businesses_verified'
    )

    plan = models.CharField(max_length=10, choices=Plan.choices, default=Plan.GRATUITO)
    plan_expires_at = models.DateTimeField(null=True, blank=True)

    # Contadores denormalizados para que el panel del negocio cargue rápido;
    # el detalle día a día vive en BusinessEvent.
    views_count = models.PositiveIntegerField(default=0)
    clicks_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    comments = GenericRelation('interactions.Comment')
    ratings = GenericRelation('interactions.Rating')
    favorites = GenericRelation('interactions.Favorite')

    class Meta:
        verbose_name = 'Negocio'
        verbose_name_plural = 'Negocios (Centro Empresarial)'
        ordering = ['-plan', '-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    @property
    def is_public(self):
        return self.status == self.Status.APROBADO

    @property
    def is_plan_active(self):
        if self.plan == self.Plan.GRATUITO:
            return True
        return bool(self.plan_expires_at and self.plan_expires_at > timezone.now())

    @property
    def effective_plan(self):
        """El plan real a efectos de ordenar resultados: si venció, cae a gratuito."""
        return self.plan if self.is_plan_active else self.Plan.GRATUITO

    def register_event(self, kind):
        BusinessEvent.objects.create(business=self, kind=kind)
        if kind == BusinessEvent.Kind.VIEW:
            Business.objects.filter(pk=self.pk).update(views_count=models.F('views_count') + 1)
        elif kind == BusinessEvent.Kind.CLICK:
            Business.objects.filter(pk=self.pk).update(clicks_count=models.F('clicks_count') + 1)


class BusinessImage(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='business/gallery/', validators=[validate_image_file])
    caption = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = 'Foto de negocio'
        verbose_name_plural = 'Galería de negocios'


class BusinessPromotion(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='promotions')
    title = models.CharField('Título', max_length=120)
    description = models.CharField('Descripción', max_length=300, blank=True)
    discount_text = models.CharField('Descuento / oferta', max_length=80, blank=True, help_text='Ej: 20% OFF, 2x1')
    valid_until = models.DateField('Válida hasta', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.business.name} · {self.title}'

    @property
    def is_expired(self):
        from datetime import date
        return bool(self.valid_until and self.valid_until < date.today())


class BusinessEvent(models.Model):
    """Registro de eventos para las estadísticas del panel empresarial."""
    class Kind(models.TextChoices):
        VIEW = 'view', 'Visita al perfil'
        CLICK = 'click', 'Clic (llamar/whatsapp/web)'
        SEARCH_APPEARANCE = 'search', 'Apareció en una búsqueda'

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='events')
    kind = models.CharField(max_length=10, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evento de negocio'
        verbose_name_plural = 'Eventos de negocio'
        indexes = [models.Index(fields=['business', 'kind', 'created_at'])]


class Subscription(models.Model):
    """
    Registro de contratación de un plan. Preparado para conectar una
    pasarela de pago real (Wompi, Mercado Pago, PayU, Stripe) más
    adelante — por ahora no procesa cobros, solo deja la estructura.
    """
    class Provider(models.TextChoices):
        WOMPI = 'wompi', 'Wompi'
        MERCADOPAGO = 'mercadopago', 'Mercado Pago'
        PAYU = 'payu', 'PayU'
        STRIPE = 'stripe', 'Stripe'
        MANUAL = 'manual', 'Registro manual (admin)'

    class PaymentStatus(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        COMPLETADO = 'completado', 'Completado'
        FALLIDO = 'fallido', 'Fallido'
        CANCELADO = 'cancelado', 'Cancelado'

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=10, choices=Business.Plan.choices)
    provider = models.CharField(max_length=15, choices=Provider.choices, default=Provider.MANUAL)
    external_reference = models.CharField('Referencia externa (pasarela)', max_length=120, blank=True)
    amount_cop = models.DecimalField('Monto (COP)', max_digits=10, decimal_places=0, default=0)
    status = models.CharField(max_length=15, choices=PaymentStatus.choices, default=PaymentStatus.PENDIENTE)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Suscripción / Pago'
        verbose_name_plural = 'Suscripciones / Pagos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.business.name} · {self.get_plan_display()} · {self.get_status_display()}'
