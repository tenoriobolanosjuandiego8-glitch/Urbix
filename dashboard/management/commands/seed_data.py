"""
dashboard/management/commands/seed_data.py
Crea datos iniciales de URBIX con información real de Popayán:
- 4 operadores reales: Transpubenza, Translibertad, Sotracauca, Transtambo
- 24 rutas reales (barrios/sectores que cubren, según información pública)
- Paraderos y lugares (barrios, universidades, hospitales, parques)
- Buses, conductores, restaurantes, hoteles, turismo, eventos

IMPORTANTE: las coordenadas de los barrios/sectores son APROXIMADAS
(ubicadas a ojo alrededor del centro de Popayán para fines de
visualización), no son coordenadas exactas geolocalizadas. Para
producción real, se recomienda corregirlas una por una desde el panel
admin o con un proceso de geocodificación (ver README).

Uso: python manage.py seed_data
"""
from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import DriverProfile
from routes.models import Route, Stop, RouteStop, ScheduleEntry, Operator
from buses.models import Bus
from restaurants.models import Restaurant
from hotels.models import Hotel
from tourism.models import TouristPlace
from events.models import Event

User = get_user_model()

CENTER = (2.4448, -76.6147)

# Nombre -> (lat, lng, categoria). Aproximadas, ver nota arriba.
STOPS_DATA = {
    'Centro':                (2.4448, -76.6147, Stop.Category.REFERENCIA),
    'Calle 5':                (2.4452, -76.6128, Stop.Category.REFERENCIA),
    'Calle 13':               (2.4468, -76.6118, Stop.Category.REFERENCIA),
    'Carrera 17':             (2.4478, -76.6098, Stop.Category.REFERENCIA),
    'Terminal de Transporte': (2.4570, -76.6070, Stop.Category.TERMINAL),
    'El Cadillal':            (2.4300, -76.6050, Stop.Category.BARRIO),
    'Ciudad Jardín':          (2.4600, -76.6130, Stop.Category.BARRIO),
    'Valencia':               (2.4650, -76.6150, Stop.Category.BARRIO),
    'Santa Teresa':           (2.4470, -76.6250, Stop.Category.BARRIO),
    'Bello Horizonte':        (2.4550, -76.6020, Stop.Category.BARRIO),
    'La Primavera':           (2.4280, -76.6180, Stop.Category.BARRIO),
    'Las Américas':           (2.4500, -76.5980, Stop.Category.BARRIO),
    'Salida hacia Timbío':    (2.4000, -76.6300, Stop.Category.REFERENCIA),
    'Valle de Pubenza':       (2.4400, -76.6300, Stop.Category.BARRIO),
    'María Occidente':        (2.4380, -76.6280, Stop.Category.BARRIO),
    'Campanario':             (2.4580, -76.6180, Stop.Category.BARRIO),
    'Lomas de Granada':       (2.4620, -76.6100, Stop.Category.BARRIO),
    'Piendamó':               (2.6350, -76.5350, Stop.Category.REFERENCIA),
    'Norte de Popayán':       (2.4680, -76.6140, Stop.Category.BARRIO),
    'La Paz':                 (2.4250, -76.6250, Stop.Category.BARRIO),
    'La Esmeralda':           (2.4600, -76.6080, Stop.Category.BARRIO),
    'Tomás Cipriano':         (2.4380, -76.6120, Stop.Category.BARRIO),
    'Modelo':                 (2.4420, -76.6180, Stop.Category.BARRIO),
    'Santa Elena':            (2.4300, -76.6150, Stop.Category.BARRIO),
    'Bolívar':                (2.4460, -76.6160, Stop.Category.BARRIO),
    'Pandiguando':            (2.4150, -76.6100, Stop.Category.BARRIO),
    'Los Naranjos':           (2.4650, -76.6200, Stop.Category.BARRIO),
    'Chirimía':                (2.4300, -76.6280, Stop.Category.BARRIO),
    'Jardines de Paz':        (2.4200, -76.6200, Stop.Category.REFERENCIA),
    'Lácteos Puracé':         (2.4150, -76.6180, Stop.Category.REFERENCIA),
    'Morinda':                (2.4550, -76.6250, Stop.Category.BARRIO),
    'La Venta':               (2.4400, -76.6350, Stop.Category.BARRIO),
    'El Tambo':               (2.4050, -76.8150, Stop.Category.REFERENCIA),
    'Cajete':                 (2.4100, -76.7800, Stop.Category.REFERENCIA),
    'Oriente':                (2.4470, -76.5950, Stop.Category.BARRIO),
    'Hospital Universitario San José': (2.4500, -76.6060, Stop.Category.HOSPITAL),
    'Universidad del Cauca':           (2.4400, -76.6015, Stop.Category.UNIVERSIDAD),
    'Parque Caldas':                   (2.4445, -76.6135, Stop.Category.PARQUE),
}

STOP_ALIASES = {'Norte': 'Norte de Popayán', 'Terminal': 'Terminal de Transporte'}

OPERATORS_DATA = {
    'Transpubenza': {
        'brand_color': '#4CFF6E', 'fleet_size': 250,
        'palette': ['#4CFF6E', '#22c55e', '#16a34a', '#34d399', '#10b981', '#4ade80', '#6ee7b7', '#2dd4bf', '#059669'],
        'routes': {
            '1 (TP1BT)':  ['La Paz', 'La Esmeralda', 'Tomás Cipriano', 'Centro', 'Parque Caldas', 'Modelo', 'Santa Elena', 'Bolívar', 'Pandiguando', 'Los Naranjos'],
            '2 (TP2BT)':  ['Tomás Cipriano', 'Chirimía', 'Centro', 'Parque Caldas', 'Campanario', 'Jardines de Paz', 'Modelo'],
            '4 (TP4BT)':  ['Centro', 'Campanario', 'Terminal', 'Bello Horizonte', 'Valle de Pubenza'],
            '5 (TP5BT)':  ['Valle de Pubenza', 'Terminal', 'Centro', 'Campanario', 'Ciudad Jardín'],
            '6 (TP6BT)':  ['La Paz', 'Lácteos Puracé', 'Calle 13', 'Centro', 'Los Naranjos'],
            '8 (TP8BT)':  ['Los Naranjos', 'Tomás Cipriano', 'La Esmeralda', 'Morinda', 'Centro', 'Valle de Pubenza'],
            '9 (TP9BT)':  ['Los Naranjos', 'Calle 13', 'Centro', 'La Venta'],
            '10 (TP10M)': ['Lomas de Granada', 'Centro', 'Campanario', 'Terminal'],
            '11 (TP11M)': ['Terminal', 'Campanario', 'Ciudad Jardín', 'Norte'],
        },
    },
    'Translibertad': {
        'brand_color': '#4dd2ff', 'fleet_size': 140,
        'palette': ['#4dd2ff', '#38bdf8', '#0ea5e9', '#22d3ee', '#0284c7', '#7dd3fc'],
        'routes': {
            '1 (TL1BT)': ['Centro', 'Parque Caldas', 'Calle 5', 'Terminal', 'El Cadillal', 'Ciudad Jardín', 'Valencia', 'Santa Teresa', 'Bello Horizonte', 'La Primavera', 'Las Américas', 'Salida hacia Timbío'],
            '2 (TL2BT)': ['Centro', 'Terminal', 'Valle de Pubenza', 'María Occidente', 'Bello Horizonte', 'Las Américas', 'Carrera 17'],
            '3 (TL3BT)': ['Centro', 'Campanario', 'Ciudad Jardín', 'Lomas de Granada', 'Bello Horizonte', 'Terminal'],
            '4 (TL4BT)': ['Centro', 'Bello Horizonte', 'Las Américas', 'Terminal', 'María Occidente', 'Santa Teresa'],
            '5 (TL5M)':  ['Piendamó', 'Terminal', 'Centro', 'Hospital Universitario San José', 'Valle de Pubenza', 'Bello Horizonte'],
            '6 (TL6BT)': ['Centro', 'Terminal', 'Norte de Popayán', 'Ciudad Jardín', 'Valencia'],
        },
    },
    'Sotracauca': {
        'brand_color': '#ffcc4d', 'fleet_size': 110,
        'palette': ['#ffcc4d', '#fbbf24', '#f59e0b', '#facc15', '#fb923c'],
        'routes': {
            '1': ['El Cadillal', 'Centro', 'Terminal', 'Valle de Pubenza'],
            '2': ['Lomas de Granada', 'Centro', 'Valle de Pubenza'],
            '7': ['Valle de Pubenza', 'Centro', 'Campanario', 'Norte'],
            '8': ['Oriente', 'Centro', 'Terminal', 'Bello Horizonte'],
            '9': ['El Cadillal', 'Carrera 17', 'Universidad del Cauca', 'Centro', 'Terminal'],
        },
    },
    'Transtambo': {
        'brand_color': '#b48cff', 'fleet_size': 70,
        'palette': ['#b48cff', '#a78bfa', '#c084fc', '#8b5cf6'],
        'routes': {
            '1': ['El Tambo', 'Cajete', 'Centro', 'Terminal', 'Valle de Pubenza'],
            '4': ['Valle de Pubenza', 'Centro', 'Campanario', 'Norte'],
            '5': ['Morinda', 'Lácteos Puracé', 'Centro', 'Lomas de Granada'],
            '6': ['El Tambo', 'Carrera 17', 'Terminal', 'Centro', 'Valle de Pubenza'],
        },
    },
}

DRIVER_NAMES = [
    ('Carlos', 'Muñoz'), ('Diana', 'Ríos'), ('Jorge', 'Salazar'), ('Laura', 'Prado'),
    ('Andrés', 'Zúñiga'), ('Marcela', 'Ordóñez'), ('Fabián', 'Rengifo'), ('Yolanda', 'Chávez'),
]


class Command(BaseCommand):
    help = 'Crea datos iniciales de ejemplo para URBIX, con las rutas reales de Popayán.'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos iniciales de URBIX...')

        self._create_users()
        stops = self._create_stops()
        operators = self._create_operators()
        routes = self._create_routes(operators, stops)
        self._create_schedules(routes)
        buses = self._create_buses(operators, routes)
        self._create_drivers(buses, routes)
        self._create_restaurants()
        self._create_hotels()
        self._create_places()
        self._create_events()

        self.stdout.write(self.style.SUCCESS(
            '¡Listo! %d operadores, %d rutas reales, %d paraderos/lugares, %d buses.' % (
                len(operators), len(routes), len(stops), len(buses))
        ))
        self.stdout.write('Superusuario: admin@urbix.co / admin12345')
        self.stdout.write('Usuario demo: usuario@urbix.co / usuario12345')
        self.stdout.write('Conductor demo: conductor@urbix.co / conductor12345')

    def _create_users(self):
        if not User.objects.filter(email='admin@urbix.co').exists():
            admin = User.objects.create_superuser(
                username='admin_urbix', email='admin@urbix.co', password='admin12345',
                first_name='Administrador', last_name='URBIX',
            )
            admin.role = User.Role.ADMIN
            admin.email_verified = True
            admin.save()

        if not User.objects.filter(email='usuario@urbix.co').exists():
            u = User.objects.create_user(
                username='usuario_demo', email='usuario@urbix.co', password='usuario12345',
                first_name='Usuario', last_name='Demo', role=User.Role.USUARIO,
            )
            u.email_verified = True
            u.save()

        if not User.objects.filter(email='conductor@urbix.co').exists():
            c = User.objects.create_user(
                username='conductor_demo', email='conductor@urbix.co', password='conductor12345',
                first_name='Carlos', last_name='Muñoz', role=User.Role.CONDUCTOR,
            )
            c.email_verified = True
            c.save()

    def _create_stops(self):
        created = {}
        for name, (lat, lng, category) in STOPS_DATA.items():
            stop, _ = Stop.objects.get_or_create(name=name, defaults={
                'latitude': lat, 'longitude': lng, 'category': category,
            })
            created[name] = stop
        return created

    def _resolve_stop(self, stops_by_name, raw_name):
        name = STOP_ALIASES.get(raw_name, raw_name)
        return stops_by_name[name]

    def _create_operators(self):
        operators = {}
        for name, data in OPERATORS_DATA.items():
            op, _ = Operator.objects.get_or_create(name=name, defaults={
                'brand_color': data['brand_color'], 'fleet_size': data['fleet_size'],
            })
            operators[name] = op
        return operators


        # Rutas REALES de Popayán (4 empresas, rutas principales)
        RUTAS_REALES = {
            'Transpubenza': [
                {
                    'name': 'Ruta 5', 'code': '005', 'color': '#FF6B6B',
                    'origin': 'Terminal Popayán', 'destination': 'Barrio Caldas',
                    'stops': ['Terminal Popayán', 'Centro', 'Parque Caldas', 'Barrio Caldas']
                },
                {
                    'name': 'Ruta 7', 'code': '007', 'color': '#FF8E72',
                    'origin': 'Barrio El Hueco', 'destination': 'Barrio Tomás Cipriani',
                    'stops': ['Barrio El Hueco', 'Centro', 'Parque Bolívar', 'Barrio Tomás Cipriani']
                },
            ],
            'Translibertad': [
                {
                    'name': 'Ruta 1', 'code': '001', 'color': '#4ECDC4',
                    'origin': 'Barrio Tequendama', 'destination': 'Centro',
                    'stops': ['Barrio Tequendama', 'Parque Caldas', 'Centro', 'Catedral']
                },
                {
                    'name': 'Ruta 3', 'code': '003', 'color': '#45B7D1',
                    'origin': 'Barrio Santander', 'destination': 'Terminal',
                    'stops': ['Barrio Santander', 'Avenida Cauca', 'Centro', 'Terminal Popayán']
                },
            ],
            'Sotracauca': [
                {
                    'name': 'Ruta 2', 'code': '002', 'color': '#95E1D3',
                    'origin': 'Barrio Bolívar', 'destination': 'Barrio Rosa María',
                    'stops': ['Barrio Bolívar', 'Avenida Norte', 'Centro', 'Barrio Rosa María']
                },
                {
                    'name': 'Ruta 6', 'code': '006', 'color': '#A8E6CF',
                    'origin': 'Barrio Pubenza', 'destination': 'Loma de la Cruz',
                    'stops': ['Barrio Pubenza', 'Carrera 8', 'Parque Caldas', 'Loma de la Cruz']
                },
            ],
            'Transtambo': [
                {
                    'name': 'Ruta 4', 'code': '004', 'color': '#FFD93D',
                    'origin': 'Barrio San Francisco', 'destination': 'Barrio La Paz',
                    'stops': ['Barrio San Francisco', 'Centro', 'Parque Bolívar', 'Barrio La Paz']
                },
                {
                    'name': 'Ruta 8', 'code': '008', 'color': '#FFEE93',
                    'origin': 'Barrio La Paz', 'destination': 'Barrio Publicano',
                    'stops': ['Barrio La Paz', 'Avenida Cauca', 'Centro', 'Barrio Publicano']
                },
            ],
        }
        
        # Coordenadas REALES de Popayán (centro ~2.4448, -76.6147)
        PARADAS_COORDS = {
            'Terminal Popayán': (2.4380, -76.6172),
            'Centro': (2.4448, -76.6147),
            'Parque Caldas': (2.4500, -76.6100),
            'Barrio Caldas': (2.4550, -76.6050),
            'Barrio El Hueco': (2.4350, -76.6200),
            'Parque Bolívar': (2.4400, -76.6100),
            'Barrio Tomás Cipriani': (2.4600, -76.6200),
            'Catedral': (2.4460, -76.6120),
            'Barrio Tequendama': (2.4300, -76.6000),
            'Avenida Cauca': (2.4420, -76.6180),
            'Barrio Santander': (2.4200, -76.5900),
            'Barrio Rosa María': (2.4700, -76.6000),
            'Barrio Bolívar': (2.4350, -76.5950),
            'Avenida Norte': (2.4520, -76.6250),
            'Barrio Pubenza': (2.4100, -76.6300),
            'Loma de la Cruz': (2.4750, -76.6300),
            'Barrio San Francisco': (2.4250, -76.5800),
            'Barrio La Paz': (2.4650, -76.5800),
            'Barrio Publicano': (2.4550, -76.5700),
        }
        
        # Crear paradas CON coordenadas
        paradas = {}
        for nombre, (lat, lng) in PARADAS_COORDS.items():
            p, _ = Stop.objects.get_or_create(
                name=nombre,
                defaults={
                    'category': Stop.Category.PARADERO,
                    'latitude': lat,
                    'longitude': lng,
                    'is_active': True,
                }
            )
            paradas[nombre] = p
        
        # Crear rutas con paradas
        for op_name, rutas_list in RUTAS_REALES.items():
            operador = Operator.objects.get(name=op_name)
            
            for ruta_info in rutas_list:
                ruta, _ = Route.objects.get_or_create(
                    operator=operador,
                    name=ruta_info['name'],
                    defaults={
                        'code': ruta_info['code'],
                        'color': ruta_info['color'],
                        'origin': ruta_info['origin'],
                        'destination': ruta_info['destination'],
                        'is_active': True,
                    }
                )
                
                # Agregar paradas en orden
                for i, stop_name in enumerate(ruta_info['stops']):
                    if stop_name in paradas:
                        RouteStop.objects.get_or_create(
                            route=ruta,
                            stop=paradas[stop_name],
                            order=i,
                        )

    def _create_routes(self, operators, stops_by_name):
        routes = []
        for op_name, data in OPERATORS_DATA.items():
            operator = operators[op_name]
            palette = data['palette']
            for i, (route_num, stop_names) in enumerate(data['routes'].items()):
                code = route_num.split('(')[-1].replace(')', '').strip() if '(' in route_num else ''
                display_name = 'Ruta ' + route_num.split(' ')[0]
                resolved_stops = [self._resolve_stop(stops_by_name, n) for n in stop_names]
                origin, destination = resolved_stops[0].name, resolved_stops[-1].name

                route, _ = Route.objects.get_or_create(
                    operator=operator, name=display_name,
                    defaults={
                        'code': code, 'origin': origin, 'destination': destination,
                        'description': origin + ' \u2192 ' + destination,
                        'color': palette[i % len(palette)],
                        'duration_minutes': 20 + len(resolved_stops) * 4,
                        'distance_km': round(2.5 + len(resolved_stops) * 1.3, 1),
                    }
                )
                for order, stop in enumerate(resolved_stops):
                    RouteStop.objects.get_or_create(route=route, stop=stop, order=order)
                routes.append(route)
        return routes

    def _create_schedules(self, routes):
        for route in routes:
            for day_type in ['habil', 'sabado', 'festivo']:
                for hour in [5, 6, 7, 8, 9]:
                    ScheduleEntry.objects.get_or_create(
                        route=route, day_type=day_type, departure_time=time(hour, 0),
                        defaults={'frequency_minutes': 10 if day_type == 'habil' else 15},
                    )

    def _create_buses(self, operators, routes):
        """2 buses de ejemplo por operador, asignados a sus primeras rutas."""
        prefixes = {'Transpubenza': 'TP', 'Translibertad': 'TL', 'Sotracauca': 'SC', 'Transtambo': 'TT'}
        buses = []
        plate_counter = 100
        for op_name, operator in operators.items():
            op_routes = [r for r in routes if r.operator_id == operator.id][:2]
            for idx, route in enumerate(op_routes):
                plate_counter += 7
                code = prefixes[op_name] + '-' + str(100 + idx * 50 + plate_counter % 90)
                plate = 'CAU-' + str(plate_counter)
                bus, _ = Bus.objects.get_or_create(code=code, defaults={
                    'plate': plate, 'capacity': 30,
                    'route': route, 'status': Bus.Status.EN_RUTA,
                })
                buses.append(bus)
        return buses

    def _create_drivers(self, buses, routes):
        conductor = User.objects.filter(email='conductor@urbix.co').first()
        if conductor and not DriverProfile.objects.filter(user=conductor).exists() and buses:
            DriverProfile.objects.create(
                user=conductor, license_number='CAU-LIC-001', status='activo',
                assigned_bus=buses[0], assigned_route=buses[0].route,
            )

        for i, bus in enumerate(buses[1:], start=1):
            if i >= len(DRIVER_NAMES):
                break
            first, last = DRIVER_NAMES[i]
            email_local = (first + '.' + last).lower()
            for a, b in [('é', 'e'), ('ú', 'u'), ('ñ', 'n'), ('í', 'i'), ('ó', 'o'), ('á', 'a')]:
                email_local = email_local.replace(a, b)
            email = email_local + '@urbix.co'
            user, created = User.objects.get_or_create(email=email, defaults={
                'username': email.split('@')[0], 'first_name': first, 'last_name': last,
                'role': User.Role.CONDUCTOR, 'email_verified': True,
            })
            if created:
                user.set_password('conductor12345')
                user.save()
            DriverProfile.objects.get_or_create(user=user, defaults={
                'license_number': 'CAU-LIC-' + str(100 + i), 'status': 'activo',
                'assigned_bus': bus, 'assigned_route': bus.route,
            })

    def _create_restaurants(self):
        data = [
            ('Parador de la Fresa', 'Gastronomía típica', 4.6, '$$', 'Vía Popayán - El Tambo Km 5',
             'Referente de la cocina payanesa desde 1980, famoso por sus postres de fresa.'),
            ('Restaurante El Mesón Payanés', 'Comida tradicional', 4.4, '$$', 'Calle 5 # 8-89, Centro',
             'Cocina tradicional caucana en una casona colonial restaurada.'),
            ('Café La Palma', 'Cafetería', 4.3, '$', 'Carrera 6 # 4-12, Centro',
             'Café de especialidad del Cauca, tostado local y repostería artesanal.'),
            ('Panadería La Repostería', 'Panadería y pastelería', 4.1, '$', 'Carrera 7 # 3-45',
             'Pan artesanal, empanadas de pipián y pastelería fina desde 1975.'),
        ]
        for name, tag, rating, price, addr, desc in data:
            Restaurant.objects.get_or_create(name=name, defaults={
                'tag': tag, 'price_range': price, 'address': addr, 'description': desc,
            })

    def _create_hotels(self):
        data = [
            ('Hotel Dann Monasterio', 220000, 'Calle 4 # 10-14, Centro Histórico',
             'Wifi, Piscina, Desayuno, Parqueadero', 'Antiguo monasterio franciscano convertido en hotel patrimonial.'),
            ('Hotel San Martín', 150000, 'Carrera 5 # 6-18',
             'Wifi, Desayuno, Recepción 24h', 'Hotel boutique de estilo colonial a pocos pasos del parque Caldas.'),
            ('Hotel Alcayata Popayán', 130000, 'Calle 2 # 6-40',
             'Wifi, Terraza, Parqueadero', 'Alojamiento moderno con terraza panorámica sobre la ciudad blanca.'),
        ]
        for name, price, addr, services, desc in data:
            Hotel.objects.get_or_create(name=name, defaults={
                'approx_price': price, 'address': addr, 'services': services, 'description': desc,
            })

    def _create_places(self):
        data = [
            ('Morro de Tulcán', 'Mirador natural e histórico',
             'Antiguo asentamiento prehispánico y hoy el mejor mirador panorámico de la ciudad.',
             'En su cima se alza una estatua ecuestre del fundador de la ciudad.'),
            ('Puente del Humilladero', 'Patrimonio histórico',
             'Construido para conectar el centro con el barrio El Callejón.',
             'Su nombre recuerda el gesto de humildad de quienes llegaban a la ciudad.'),
            ('Centro Histórico de Popayán', 'Patrimonio cultural',
             'Declarado Patrimonio Histórico de la Humanidad por sus fachadas blancas coloniales.',
             'Escenario de la Semana Santa, patrimonio inmaterial de la UNESCO.'),
            ('Torre del Reloj', 'Símbolo de la ciudad',
             'Reconstruida tras el terremoto de 1983, es uno de los íconos más fotografiados.',
             'Su reloj fue traído originalmente desde Inglaterra en el siglo XIX.'),
        ]
        for name, tag, history, curiosities in data:
            TouristPlace.objects.get_or_create(name=name, defaults={
                'tag': tag, 'history': history, 'curiosities': curiosities,
            })

    def _create_events(self):
        now = timezone.now()
        data = [
            ('Semana Santa Popayán', Event.Category.RELIGIOSO, 'Centro Histórico', now + timedelta(days=5),
             'Procesiones patrimoniales declaradas por la UNESCO, recorriendo el centro colonial.'),
            ('Festival Gastronómico', Event.Category.GASTRONOMICO, 'Parque Caldas', now + timedelta(days=11),
             'Muestra de gastronomía típica caucana con más de 40 expositores locales.'),
            ('Concierto en el Parque', Event.Category.MUSICAL, 'Parque Caldas', now + timedelta(days=18),
             'Agrupaciones locales e invitados nacionales en una noche de música en vivo.'),
        ]
        for name, category, place, start_at, desc in data:
            Event.objects.get_or_create(name=name, defaults={
                'category': category, 'place': place, 'start_at': start_at, 'description': desc,
            })
