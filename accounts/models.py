"""
accounts/models.py
Usuario personalizado con roles (usuario, conductor, administrador)
y perfil extendido de conductor.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from accounts.validators import validate_image_file
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Usuario de URBIX. Extiende el usuario base de Django agregando
    rol, teléfono, foto de perfil y verificación de correo.
    """

    class Role(models.TextChoices):
        USUARIO = 'usuario', _('Usuario')
        CONDUCTOR = 'conductor', _('Conductor')
        EMPRESA = 'empresa', _('Empresa')
        ADMIN = 'administrador', _('Administrador')

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USUARIO)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=80, default='Popayán', blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, validators=[validate_image_file])
    email_verified = models.BooleanField(default=False)
    remember_session = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_driver(self):
        return self.role == self.Role.CONDUCTOR

    @property
    def is_urbix_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser


class DriverProfile(models.Model):
    """Información adicional específica de los conductores."""

    class Status(models.TextChoices):
        ACTIVE = 'activo', _('Activo')
        INACTIVE = 'inactivo', _('Inactivo')
        SUSPENDED = 'suspendido', _('Suspendido')

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='driver_profile',
        limit_choices_to={'role': User.Role.CONDUCTOR}
    )
    license_number = models.CharField('Número de licencia', max_length=40, unique=True)
    license_expiry = models.DateField('Vencimiento de licencia', null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    assigned_bus = models.ForeignKey(
        'buses.Bus', on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers'
    )
    assigned_route = models.ForeignKey(
        'routes.Route', on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers'
    )
    hired_at = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Perfil de conductor'
        verbose_name_plural = 'Perfiles de conductores'

    def __str__(self):
        return f'{self.user.get_full_name()} · {self.license_number}'


class ActivityLog(models.Model):
    """Bitácora simple de actividad de usuarios (requisito de seguridad)."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de actividad'
        verbose_name_plural = 'Registros de actividad'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} {self.method} {self.path} @ {self.created_at:%Y-%m-%d %H:%M}'


class EmergencyContact(models.Model):
    """Contacto de emergencia del usuario, usado por el botón SOS."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField('Nombre', max_length=100)
    phone = models.CharField('Teléfono', max_length=30)
    relationship = models.CharField('Relación', max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Contacto de emergencia'
        verbose_name_plural = 'Contactos de emergencia'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.user})'


class LoginAttempt(models.Model):
    """
    Registra intentos de inicio de sesión fallidos para bloquear
    temporalmente después de varios intentos seguidos (protección
    contra ataques de fuerza bruta). Se limpia solo con el tiempo:
    solo se consultan los últimos LOCKOUT_WINDOW_MINUTES.
    """
    LOCKOUT_THRESHOLD = 5
    LOCKOUT_WINDOW_MINUTES = 15

    email = models.EmailField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Intento de inicio de sesión'
        verbose_name_plural = 'Intentos de inicio de sesión'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['email', 'created_at'])]

    def __str__(self):
        return f'{self.email} · {"OK" if self.success else "fallido"} · {self.created_at:%Y-%m-%d %H:%M}'

    @classmethod
    def is_locked_out(cls, email, ip_address=None):
        from django.utils import timezone
        from datetime import timedelta
        window_start = timezone.now() - timedelta(minutes=cls.LOCKOUT_WINDOW_MINUTES)
        recent_failed = cls.objects.filter(email__iexact=email, success=False, created_at__gte=window_start).count()
        return recent_failed >= cls.LOCKOUT_THRESHOLD

    @classmethod
    def record(cls, email, ip_address, success):
        cls.objects.create(email=email, ip_address=ip_address, success=success)
        if success:
            # Un login exitoso limpia el contador de intentos fallidos recientes
            from django.utils import timezone
            from datetime import timedelta
            window_start = timezone.now() - timedelta(minutes=cls.LOCKOUT_WINDOW_MINUTES)
            cls.objects.filter(email__iexact=email, success=False, created_at__gte=window_start).delete()
