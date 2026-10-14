from django.test import TestCase, Client
from django.urls import reverse
from .models import Route, Stop, RouteStop


class RouteModelTests(TestCase):
    def setUp(self):
        self.stop_a = Stop.objects.create(name='Centro', latitude=2.4448, longitude=-76.6147)
        self.stop_b = Stop.objects.create(name='Terminal', latitude=2.4570, longitude=-76.6070)
        self.route = Route.objects.create(
            name='Ruta 1', origin='Centro', destination='Terminal',
            color='#4CFF6E', duration_minutes=45, distance_km=12.5,
        )
        RouteStop.objects.create(route=self.route, stop=self.stop_a, order=0)
        RouteStop.objects.create(route=self.route, stop=self.stop_b, order=1)

    def test_path_coordinates_ordered(self):
        path = self.route.path_coordinates
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0], [2.4448, -76.6147])
        self.assertEqual(path[1], [2.4570, -76.6070])

    def test_route_list_view_status_code(self):
        response = self.client.get(reverse('routes:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ruta 1')


class MapViewTests(TestCase):
    def test_map_data_endpoint_returns_json(self):
        Route.objects.create(name='Ruta 1', origin='A', destination='B', color='#4CFF6E')
        response = self.client.get(reverse('map:data'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('routes', data)
        self.assertIn('buses', data)
