"""
accounts/decorators.py
Decoradores para restringir vistas según el rol del usuario.
Cada rol ve únicamente las opciones que le corresponden.
"""
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles and not request.user.is_superuser:
                messages.error(request, 'No tienes permiso para acceder a esta sección.')
                return redirect('dashboard:redirect')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    return role_required('administrador')(view_func)


def business_required(view_func):
    return role_required('empresa')(view_func)


def driver_required(view_func):
    return role_required('conductor')(view_func)


def user_required(view_func):
    return role_required('usuario')(view_func)
