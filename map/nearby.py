"""
map/nearby.py
"Sitios cercanos" — farmacias, cajeros, gasolineras, supermercados,
etc. cerca del usuario, usando la API gratuita de Geoapify (no
guardamos estos datos en nuestra base, los consultamos en el momento).

Requiere una clave gratuita (sin tarjeta) en:
https://www.geoapify.com — variable GEOAPIFY_API_KEY en tu .env.
"""
import json
import os
import urllib.parse
import urllib.request

from django.http import JsonResponse

CATEGORY_MAP = {
    'farmacia': 'healthcare.pharmacy',
    'cajero': 'service.financial.atm',
    'gasolinera': 'service.vehicle.fuel',
    'supermercado': 'commercial.supermarket',
    'hospital': 'healthcare.hospital',
    'universidad': 'education.university',
    'centro_comercial': 'commercial.shopping_mall',
    'restaurante': 'catering.restaurant',
}


def nearby_places(request):
    """GET ?categoria=farmacia&lat=..&lng=..&radio=1000"""
    api_key = os.environ.get('GEOAPIFY_API_KEY')
    if not api_key:
        return JsonResponse({
            'error': 'Sitios cercanos aún no está activado (falta GEOAPIFY_API_KEY en el .env).',
            'places': [],
        }, status=200)

    categoria = request.GET.get('categoria', 'farmacia')
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radio = request.GET.get('radio', '1000')

    if not lat or not lng:
        return JsonResponse({'error': 'Faltan coordenadas.', 'places': []}, status=400)

    geoapify_category = CATEGORY_MAP.get(categoria, 'commercial')
    params = {
        'categories': geoapify_category,
        'filter': f'circle:{lng},{lat},{radio}',
        'bias': f'proximity:{lng},{lat}',
        'limit': 20,
        'apiKey': api_key,
    }
    url = 'https://api.geoapify.com/v2/places?' + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        return JsonResponse({'error': f'No se pudo consultar Geoapify: {exc}', 'places': []}, status=200)

    places = []
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates', [None, None])
        places.append({
            'name': props.get('name') or props.get('address_line1') or 'Sin nombre',
            'address': props.get('address_line2') or props.get('formatted', ''),
            'lat': coords[1], 'lng': coords[0],
            'distance_m': props.get('distance'),
        })

    return JsonResponse({'places': places, 'category': categoria})
