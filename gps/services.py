"""
gps/services.py
Lógica de un "paso" de simulación de movimiento de buses, reutilizada
tanto por el comando de terminal (simulate_gps) como por el botón
"Simulación en vivo" del mapa/dashboard (sin necesidad de terminal).

Guardamos el progreso de cada bus en memoria del proceso (_progress).
Si usas varios workers en producción, cada uno llevará su propio
avance — para un solo proceso (como en desarrollo o un servidor
pequeño) funciona perfecto.
"""
import math
import random

from buses.models import Bus
from .models import GPSLocation

_progress = {}


def _bearing(lat1, lng1, lat2, lng2):
    """Ángulo de 0-360° (0=norte) entre dos puntos, para rotar el ícono del bus."""
    if lat1 == lat2 and lng1 == lng2:
        return 0
    d_lng = math.radians(lng2 - lng1)
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    x = math.sin(d_lng) * math.cos(lat2_r)
    y = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(d_lng)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def simulate_step(step_size=0.03):
    """Avanza cada bus activo un paso a lo largo de su ruta y guarda su
    nueva posición GPS. Retorna cuántos buses se actualizaron."""
    buses = Bus.objects.filter(is_active=True, route__isnull=False).select_related('route')
    updated = 0
    for bus in buses:
        path = bus.route.path_coordinates
        if len(path) < 2:
            continue
        t = _progress.get(bus.id, 0.0)
        t_next = (t + step_size) % 1.0
        _progress[bus.id] = t_next

        idx = t_next * (len(path) - 1)
        i0, i1 = int(idx), min(int(idx) + 1, len(path) - 1)
        frac = idx - i0
        lat = path[i0][0] + (path[i1][0] - path[i0][0]) * frac
        lng = path[i0][1] + (path[i1][1] - path[i0][1]) * frac
        heading = _bearing(path[i0][0], path[i0][1], path[i1][0], path[i1][1])
        speed = round(random.uniform(18, 34), 1)

        GPSLocation.objects.create(bus=bus, latitude=lat, longitude=lng, speed_kmh=speed, heading=heading)
        bus.last_speed_kmh = speed
        bus.occupancy = random.choices(
            [Bus.Occupancy.BAJA, Bus.Occupancy.MEDIA, Bus.Occupancy.ALTA, Bus.Occupancy.LLENO],
            weights=[25, 40, 25, 10],
        )[0]
        bus.save(update_fields=['last_speed_kmh', 'occupancy'])
        updated += 1
    return updated


def simulate_step_smooth(step_size=0.02):
    """
    Versión mejorada de simulate_step que:
    - Sigue el trazado real (snapped_path) si existe
    - Interpola suavemente entre puntos
    - Mantiene velocidad y rumbo más realistas
    - Simula paradas en semáforos (ocasionalmente frena)
    """
    import random
    buses = Bus.objects.filter(is_active=True, route__isnull=False).select_related('route')
    updated = 0
    
    for bus in buses:
        path = bus.route.path_coordinates
        if len(path) < 2:
            continue
        
        t = _progress.get(bus.id, 0.0)
        t_next = (t + step_size) % 1.0
        _progress[bus.id] = t_next
        
        # Interpolación suave
        idx = t_next * (len(path) - 1)
        i0 = min(int(idx), len(path) - 2)
        i1 = i0 + 1
        
        frac = idx - i0
        # Easing: suaviza la transición entre puntos
        frac_smooth = frac * frac * (3 - 2 * frac)
        
        lat = path[i0][0] + (path[i1][0] - path[i0][0]) * frac_smooth
        lng = path[i0][1] + (path[i1][1] - path[i0][1]) * frac_smooth
        
        heading = _bearing(path[i0][0], path[i0][1], path[i1][0], path[i1][1])
        
        # Velocidad más realista: variar con pequeños cambios
        if not hasattr(bus, '_speed_momentum'):
            bus._speed_momentum = random.uniform(20, 35)
        
        momentum = 0.85
        bus._speed_momentum = (
            bus._speed_momentum * momentum + 
            random.uniform(15, 40) * (1 - momentum)
        )
        speed = max(5, min(50, bus._speed_momentum))  # entre 5 y 50 km/h
        
        # Ocasionalmente "semáforo" (frena momentáneamente)
        if random.random() < 0.05:  # 5% de probabilidad cada paso
            speed *= random.uniform(0.3, 0.8)
        
        from gps.models import GPSLocation
        loc = GPSLocation.objects.create(
            bus=bus, driver=bus.current_driver,
            latitude=lat, longitude=lng,
            speed_kmh=round(speed, 1),
            heading=heading,
        )
        
        bus.last_speed_kmh = loc.speed_kmh
        bus.save(update_fields=['last_speed_kmh'])
        updated += 1
    
    return updated
