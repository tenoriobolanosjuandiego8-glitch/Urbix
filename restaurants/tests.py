from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Restaurant

User = get_user_model()


class RestaurantPublicTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Parador de la Fresa', tag='Gastronomía típica', address='Vía El Tambo',
        )

    def test_list_view_shows_active_restaurant(self):
        response = self.client.get(reverse('restaurants:list'))
        self.assertContains(response, 'Parador de la Fresa')

    def test_detail_view_status_code(self):
        response = self.client.get(reverse('restaurants:detail', args=[self.restaurant.pk]))
        self.assertEqual(response.status_code, 200)


class RestaurantAdminCRUDTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_r', email='admin_r@example.com', password='ClaveSegura123', role=User.Role.ADMIN)
        self.user = User.objects.create_user(
            username='user_r', email='user_r@example.com', password='ClaveSegura123', role=User.Role.USUARIO)

    def test_regular_user_cannot_create_restaurant(self):
        self.client.login(username='user_r', password='ClaveSegura123')
        response = self.client.get(reverse('restaurants:create'))
        self.assertEqual(response.status_code, 302)

    def test_admin_can_create_restaurant(self):
        self.client.login(username='admin_r', password='ClaveSegura123')
        response = self.client.post(reverse('restaurants:create'), {
            'name': 'Nuevo restaurante', 'tag': 'Comida rápida', 'address': 'Calle 1',
            'price_range': '$$', 'opening_hours': '10:00 a.m. - 8:00 p.m.', 'is_active': True,
        })
        self.assertEqual(Restaurant.objects.filter(name='Nuevo restaurante').count(), 1)
