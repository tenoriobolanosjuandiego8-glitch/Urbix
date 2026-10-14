"""
accounts/middleware.py
Middleware ligero que registra la actividad de los usuarios autenticados
(requisito de seguridad: registro de actividad).
"""
import logging

activity_logger = logging.getLogger('urbix.activity')

# Prefijos que no se registran para no llenar el log de ruido
IGNORED_PREFIXES = ('/static/', '/media/', '/admin/jsi18n/')


class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if not request.path.startswith(IGNORED_PREFIXES):
                self._log(request)
        except Exception:  # nunca debe romper la petición por un fallo de logging
            pass
        return response

    def _log(self, request):
        from .models import ActivityLog

        user = request.user if request.user.is_authenticated else None
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        activity_logger.info('%s %s %s', user, request.method, request.path)
        if user is not None and request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            # Solo persistimos en BD las acciones que modifican datos,
            # para no sobrecargar la tabla con cada GET.
            ActivityLog.objects.create(
                user=user, path=request.path[:255], method=request.method, ip_address=ip
            )
