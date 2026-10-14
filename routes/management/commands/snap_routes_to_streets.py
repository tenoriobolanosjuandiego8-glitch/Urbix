"""
routes/management/commands/snap_routes_to_streets.py
Calcula el recorrido REAL de cada ruta siguiendo las calles (como
Uber/inDriver/Didi), usando la API gratuita de OpenRouteService, y lo
guarda en Route.snapped_path. El mapa usa automáticamente ese trazado
en vez de líneas rectas entre paraderos cuando está disponible.

Requisito: una clave gratuita de https://openrouteservice.org/dev/#/signup
(no pide tarjeta de crédito) puesta en tu archivo .env como:
    OPENROUTESERVICE_API_KEY=tu-clave-aqui

Uso: python manage.py snap_routes_to_streets
     python manage.py snap_routes_to_streets --route-id 5   (solo una ruta)
"""
import json
import os
import time
import urllib.request
import urllib.error

from django.core.management.base import BaseCommand
from routes.models import Route

ORS_URL = 'https://api.openrouteservice.org/v2/directions/driving-car/geojson'


class Command(BaseCommand):
    help = 'Calcula el recorrido real (siguiendo calles) de las rutas usando OpenRouteService.'

    def add_arguments(self, parser):
        parser.add_argument('--route-id', type=int, default=None, help='Solo procesar esta ruta (ID)')

    def handle(self, *args, **options):
        api_key = os.environ.get('OPENROUTESERVICE_API_KEY')
        if not api_key:
            self.stderr.write(self.style.ERROR(
                'Falta OPENROUTESERVICE_API_KEY en tu .env. Consigue una clave gratis en '
                'https://openrouteservice.org/dev/#/signup (no pide tarjeta) y agrégala.'
            ))
            return

        qs = Route.objects.filter(is_active=True)
        if options['route_id']:
            qs = qs.filter(pk=options['route_id'])

        ok, failed = 0, 0
        for route in qs:
            stops = [[rs.stop.longitude, rs.stop.latitude]  # ORS usa [lng, lat]
                     for rs in route.routestop_set.select_related('stop').order_by('order')]
            if len(stops) < 2:
                continue
            try:
                path = self._fetch_ors_path(stops, api_key)
                route.snapped_path = path
                route.save(update_fields=['snapped_path'])
                ok += 1
                self.stdout.write(f'OK: {route}')
            except Exception as exc:
                failed += 1
                self.stderr.write(self.style.WARNING(f'Falló {route}: {exc} (se usará línea recta como respaldo)'))
            time.sleep(1.5)  # respeta el límite de peticiones del plan gratis

        self.stdout.write(self.style.SUCCESS(f'Listo: {ok} rutas actualizadas, {failed} fallaron.'))

    def _fetch_ors_path(self, coordinates, api_key):
        body = json.dumps({'coordinates': coordinates}).encode()
        req = urllib.request.Request(ORS_URL, data=body, method='POST', headers={
            'Authorization': api_key,
            'Content-Type': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
        # GeoJSON viene como [lng, lat]; Leaflet espera [lat, lng]
        coords = data['features'][0]['geometry']['coordinates']
        return [[lat, lng] for lng, lat in coords]
