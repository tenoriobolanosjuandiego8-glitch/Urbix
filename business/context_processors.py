"""
business/context_processors.py
Inyecta el conteo de negocios pendientes de verificación, para el
badge en el menú del administrador.
"""
def pending_businesses(request):
    if not request.user.is_authenticated:
        return {}
    if not (getattr(request.user, 'is_urbix_admin', False)):
        return {}
    from .models import Business
    return {'pending_businesses_count': Business.objects.filter(status=Business.Status.PENDIENTE).count()}
