"""
notifications/push.py
Envío real de notificaciones push (Web Push API) a los navegadores
suscritos de un usuario. Si el usuario no tiene ninguna suscripción
activa (nunca aceptó las notificaciones, o las desactivó), simplemente
no se envía nada — no rompe el flujo normal de crear una Notification.
"""
import json
import logging
import os

from django.conf import settings

logger = logging.getLogger('urbix.push')


def _vapid_configured():
    return bool(os.environ.get('VAPID_PUBLIC_KEY') and os.environ.get('VAPID_PRIVATE_KEY'))


def send_push_to_user(user, title, body, url='/notificaciones/'):
    """Envía un push a todos los dispositivos suscritos de un usuario.
    Silencioso si no hay claves VAPID configuradas o el usuario no
    tiene suscripciones — nunca lanza una excepción hacia arriba."""
    if not _vapid_configured():
        return 0

    from pywebpush import webpush, WebPushException
    from .models import PushSubscription

    sent = 0
    for sub in PushSubscription.objects.filter(user=user):
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=json.dumps({'title': title, 'body': body, 'url': url}),
                vapid_private_key=os.environ['VAPID_PRIVATE_KEY'],
                vapid_claims={'sub': f"mailto:{os.environ.get('VAPID_ADMIN_EMAIL', 'soporte@urbix.co')}"},
            )
            sent += 1
        except WebPushException as exc:
            status = getattr(exc.response, 'status_code', None)
            if status in (404, 410):
                # La suscripción ya no es válida (el usuario desinstaló/bloqueó) — la limpiamos.
                sub.delete()
            else:
                logger.warning('Push falló para %s: %s', user, exc)
    return sent
