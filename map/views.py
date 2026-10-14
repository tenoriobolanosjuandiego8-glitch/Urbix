"""
map/views.py
Sirve la página del mapa y un endpoint JSON con rutas, paraderos y
posición actual de cada bus, para que Leaflet los dibuje sin recargar
la página.
"""
from django.http import JsonResponse
from django.shortcuts import render, redirect

from accounts.decorators import driver_required

from buses.models import Bus
from routes.models import Route, Stop


def map_page(request):
    routes = Route.objects.filter(is_active=True)
    return render(request, 'map/mapa.html', {'routes': routes})


def map_data(request):
    routes = []
    for r in Route.objects.filter(is_active=True).select_related('operator').prefetch_related('routestop_set__stop'):
        routes.append({
            'id': r.id, 'name': r.name, 'code': r.code,
            'operator': r.operator.name if r.operator else '',
            'desc': f'{r.origin} - {r.destination}',
            'color': r.color, 'duration': f'{r.duration_minutes} min',
            'stops': r.routestop_set.count(),
            'path': r.path_coordinates,
        })

    buses = []
    for b in Bus.objects.filter(is_active=True).select_related('route', 'route__operator'):
        pos = b.last_position
        driver = b.current_driver
        if not pos:
            continue
        buses.append({
            'id': b.code, 'route': b.route_id, 'operator': b.operator_name,
            'driver': driver.user.get_full_name() if driver else 'Sin asignar',
            'status': b.get_status_display(),
            'speed': f'{pos.speed_kmh:.0f} km/h',
            'occupancy': b.get_occupancy_display(),
            'heading': pos.heading,
            'pos': [pos.latitude, pos.longitude],
        })

    stops = [{
        'id': s.id, 'name': s.name, 'category': s.get_category_display(),
        'pos': [s.latitude, s.longitude],
    } for s in Stop.objects.filter(is_active=True)]

    return JsonResponse({'routes': routes, 'buses': buses, 'stops': stops})


@driver_required
def mapaconductor(request):
    perfil = getattr(request.user, 'driver_profile', None)
    bus = perfil.assigned_bus if perfil else None
    ruta = perfil.assigned_route if perfil else None
    if ruta is None and bus is not None:
        ruta = bus.route
    paradas = []
    if ruta:
        paradas = [{'name': rs.stop.name, 'pos': [rs.stop.latitude, rs.stop.longitude]}
                   for rs in ruta.routestop_set.select_related('stop').order_by('order')]
    return render(request, 'map/conductor.html', {
        'bus': bus, 'ruta': ruta, 'trazado': ruta.path_coordinates if ruta else [],
        'paradas': paradas,
    })
