"""
notifications/context_processors.py
Inyecta el conteo de notificaciones no leídas y las últimas 5 en cada
plantilla, para el centro de notificaciones del navbar.
"""
def unread_notifications(request):
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0, 'recent_notifications': []}
    from .models import Notification
    qs = Notification.objects.filter(user=request.user)
    return {
        'unread_notifications_count': qs.filter(is_read=False).count(),
        'recent_notifications': qs[:6],
    }
