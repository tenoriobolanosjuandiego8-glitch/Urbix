"""
gps/views.py
Endpoint para que la app del conductor (con sesión iniciada en el
navegador) reporte su ubicación desde el mapa. Para integraciones de
hardware GPS / apps móviles nativas, usar el endpoint autenticado por
token en /api/v1/gps/ (ver api/views.py) en vez de este — ese sí está
pensado para clientes que no manejan cookies de sesión ni CSRF.

SEGURIDAD: este endpoint requiere sesión autenticada (@driver_required)
Y token CSRF válido (sin csrf_exempt). Combinar autenticación por
sesión con CSRF desactivado permitiría que un sitio malicioso hiciera
que el navegador de un conductor logueado enviara ubicaciones falsas
sin que él lo note — por eso NO se usa csrf_exempt aquí.
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.decorators import driver_required
from buses.models import Bus
from .models import GPSLocation


@driver_required
@require_POST
def report_location(request):
    try:
        data = json.loads(request.body or '{}')
        bus = Bus.objects.get(pk=data['bus_id'])

        # Un conductor solo puede reportar la posición del bus que tiene asignado.
        profile = getattr(request.user, 'driver_profile', None)
        if not profile or profile.assigned_bus_id != bus.id:
            return JsonResponse({'ok': False, 'error': 'No tienes asignado este bus.'}, status=403)

        lat, lng = float(data['lat']), float(data['lng'])
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return JsonResponse({'ok': False, 'error': 'Coordenadas fuera de rango.'}, status=400)

        loc = GPSLocation.objects.create(
            bus=bus, driver=request.user, latitude=lat, longitude=lng,
            speed_kmh=max(0, float(data.get('speed', 0))),
            heading=float(data.get('heading', 0)) % 360,
        )
        bus.last_speed_kmh = loc.speed_kmh
        bus.save(update_fields=['last_speed_kmh'])
        return JsonResponse({'ok': True, 'id': loc.id})
    except (KeyError, ValueError, Bus.DoesNotExist) as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
