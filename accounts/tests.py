from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterLoginTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_creates_user_with_default_role(self):
        response = self.client.post(reverse('accounts:register'), {
            'name': 'Ana Torres', 'email': 'ana@example.com',
            'password1': 'ClaveSegura123', 'password2': 'ClaveSegura123', 'terms': True,
        })
        self.assertEqual(User.objects.filter(email='ana@example.com').count(), 1)
        user = User.objects.get(email='ana@example.com')
        self.assertEqual(user.role, User.Role.USUARIO)

    def test_login_with_email_and_correct_password(self):
        user = User.objects.create_user(username='pedro', email='pedro@example.com', password='ClaveSegura123')
        response = self.client.post(reverse('accounts:login'), {
            'email': 'pedro@example.com', 'password': 'ClaveSegura123', 'remember': True,
        })
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_wrong_password_fails(self):
        User.objects.create_user(username='luis', email='luis@example.com', password='ClaveSegura123')
        response = self.client.post(reverse('accounts:login'), {
            'email': 'luis@example.com', 'password': 'incorrecta',
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class RolePermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin1', email='admin1@example.com', password='ClaveSegura123', role=User.Role.ADMIN)
        self.regular = User.objects.create_user(
            username='user1', email='user1@example.com', password='ClaveSegura123', role=User.Role.USUARIO)

    def test_regular_user_cannot_access_admin_dashboard(self):
        self.client.login(username='user1', password='ClaveSegura123')
        response = self.client.get(reverse('dashboard:admin'))
        self.assertEqual(response.status_code, 302)  # redirigido, sin permiso

    def test_admin_can_access_admin_dashboard(self):
        self.client.login(username='admin1', password='ClaveSegura123')
        response = self.client.get(reverse('dashboard:admin'))
        self.assertEqual(response.status_code, 200)
