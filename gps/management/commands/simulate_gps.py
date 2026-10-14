"""
gps/management/commands/simulate_gps.py
Simula el movimiento de los buses a lo largo de su ruta, generando
puntos GPS periódicos. Útil mientras no hay hardware GPS real conectado.
Alternativa sin terminal: botón "Simulación en vivo" en /mapa/.

Uso: python manage.py simulate_gps --interval 5
"""
import time

from django.core.management.base import BaseCommand
from gps.services import simulate_step


class Command(BaseCommand):
    help = 'Simula movimiento GPS de los buses activos a lo largo de su ruta.'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=5, help='Segundos entre actualizaciones')
        parser.add_argument('--once', action='store_true', help='Ejecuta una sola ronda y termina')

    def handle(self, *args, **options):
        interval = options['interval']
        while True:
            updated = simulate_step()
            self.stdout.write(self.style.SUCCESS(f'Actualizados {updated} buses.'))
            if options['once']:
                break
            time.sleep(interval)
