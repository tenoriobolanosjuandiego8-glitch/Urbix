"""
routes/management/commands/snap_routes_improved.py

Versión mejorada que:
1. Intenta usar OpenRouteService para rutas reales
2. Si falla, usa interpolación suave entre paradas
3. Muestra progreso detallado
"""
import json, os, time, urllib.request, urllib.error
from django.core.management.base import BaseCommand
from routes.models import Route

ORS_URL = 'https://api.openrouteservice.org/v2/directions/driving-car/geojson'

class Command(BaseCommand):
    help = 'Calcula trazados reales de rutas. Intenta OpenRouteService, respaldo a interpolación.'

    def add_arguments(self, parser):
        parser.add_argument('--route-id', type=int, default=None)
        parser.add_argument('--force', action='store_true', help='Recalcular incluso si ya tiene trazado')

    def handle(self, *args, **options):
        api_key = os.environ.get('OPENROUTESERVICE_API_KEY')
        
        qs = Route.objects.filter(is_active=True)
        if options['route_id']:
            qs = qs.filter(pk=options['route_id'])
        if not options['force']:
            qs = qs.filter(snapped_path__isnull=True)
        
        ok, fallback, skipped = 0, 0, 0
        
        for route in qs:
            stops = [[rs.stop.longitude, rs.stop.latitude]
                     for rs in route.routestop_set.select_related('stop').order_by('order')]
            
            if len(stops) < 2:
                skipped += 1
                continue
            
            # Intentar OpenRouteService
            path = None
            if api_key:
                try:
                    path = self._fetch_ors_path(stops, api_key)
                    ok += 1
                    self.stdout.write(f'✓ {route.name} (OpenRouteService)')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ORS falló: {e}, usando fallback'))
            
            # Fallback: interpolación suave
            if not path:
                path = self._interpolate_path(stops)
                fallback += 1
                self.stdout.write(f'↻ {route.name} (interpolación suave)')
            
            route.snapped_path = path
            route.save(update_fields=['snapped_path'])
            time.sleep(0.5)
        
        self.stdout.write(self.style.SUCCESS(
            f'Listo: {ok} OpenRouteService, {fallback} interpoladas, {skipped} saltadas'
        ))

    def _fetch_ors_path(self, coordinates, api_key):
        body = json.dumps({'coordinates': coordinates}).encode()
        req = urllib.request.Request(ORS_URL, data=body, method='POST', headers={
            'Authorization': api_key, 'Content-Type': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        coords = data['features'][0]['geometry']['coordinates']
        return [[lat, lng] for lng, lat in coords]

    def _interpolate_path(self, stops):
        """Interpola suavemente entre paradas para simular calles"""
        if len(stops) < 2:
            return []
        
        path = []
        puntos_por_segmento = 15  # puntos entre cada parada
        
        for i in range(len(stops) - 1):
            lng0, lat0 = stops[i]
            lng1, lat1 = stops[i + 1]
            
            for t in range(puntos_por_segmento):
                frac = t / puntos_por_segmento
                lat = lat0 + (lat1 - lat0) * frac
                lng = lng0 + (lng1 - lng0) * frac
                path.append([lat, lng])
        
        # Agregar última parada
        path.append([stops[-1][1], stops[-1][0]])
        return path
