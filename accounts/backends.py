"""
accounts/backends.py
Permite iniciar sesión usando el correo electrónico (tal como lo pide
el formulario de login del frontend) en lugar del username interno.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email', username)
        if email is None or password is None:
            return None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email__iexact=email).order_by('id').first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
