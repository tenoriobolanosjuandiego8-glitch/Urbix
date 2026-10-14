"""
notifications/management/commands/generate_vapid_keys.py
Genera el par de claves VAPID necesario para enviar notificaciones
push reales (Web Push API). Se genera UNA sola vez para todo el
proyecto — no por usuario.

Uso: python manage.py generate_vapid_keys
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Genera un par de claves VAPID para notificaciones push y las muestra en pantalla.'

    def handle(self, *args, **options):
        try:
            from py_vapid import Vapid
        except ImportError:
            self.stderr.write(self.style.ERROR(
                'Falta la librería py_vapid (viene incluida con pywebpush). '
                'Corre: pip install -r requirements.txt'
            ))
            return

        import base64
        vapid = Vapid()
        vapid.generate_keys()

        private_raw = vapid.private_key.private_numbers().private_value.to_bytes(32, 'big')
        private_b64 = base64.urlsafe_b64encode(private_raw).rstrip(b'=').decode()

        public_numbers = vapid.public_key.public_numbers()
        x = public_numbers.x.to_bytes(32, 'big')
        y = public_numbers.y.to_bytes(32, 'big')
        public_raw = b'\x04' + x + y
        public_b64 = base64.urlsafe_b64encode(public_raw).rstrip(b'=').decode()

        self.stdout.write(self.style.SUCCESS('¡Claves generadas! Agrega estas 3 líneas a tu archivo .env:\n'))
        self.stdout.write(f'VAPID_PUBLIC_KEY={public_b64}')
        self.stdout.write(f'VAPID_PRIVATE_KEY={private_b64}')
        self.stdout.write('VAPID_ADMIN_EMAIL=tu-correo@ejemplo.com')
        self.stdout.write(self.style.WARNING(
            '\nGuárdalas bien — si las pierdes, todos los usuarios tendrán que '
            'volver a activar las notificaciones push.'
        ))
