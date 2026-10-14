"""notifications/views.py"""
import json
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Notification, PushSubscription


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    vapid_public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
    return render(request, 'notifications/notificaciones.html', {
        'notifications': notifications, 'vapid_public_key': vapid_public_key,
    })


@login_required
def mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications:list')


@login_required
@require_POST
def push_subscribe(request):
    """El navegador manda aquí los datos de su suscripción push tras
    aceptar el permiso de notificaciones."""
    try:
        data = json.loads(request.body)
        PushSubscription.objects.update_or_create(
            endpoint=data['endpoint'],
            defaults={
                'user': request.user,
                'p256dh': data['keys']['p256dh'],
                'auth': data['keys']['auth'],
            },
        )
        return JsonResponse({'ok': True})
    except (KeyError, json.JSONDecodeError) as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)


@login_required
@require_POST
def push_unsubscribe(request):
    endpoint = json.loads(request.body or '{}').get('endpoint')
    if endpoint:
        PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return JsonResponse({'ok': True})


@login_required
def crear_alerta(request):
    from .models import Alerta
    from routes.models import Stop, Route
    
    if request.method == 'POST':
        parada_id = request.POST.get('parada')
        ruta_id = request.POST.get('ruta')
        tipo = request.POST.get('tipo', 'llegada_bus')
        
        parada = Stop.objects.get(pk=parada_id)
        ruta = Route.objects.get(pk=ruta_id) if ruta_id else None
        
        alerta, creada = Alerta.objects.get_or_create(
            usuario=request.user,
            parada=parada,
            ruta=ruta,
            tipo=tipo,
            defaults={'activa': True}
        )
        
        if not creada:
            alerta.activa = True
            alerta.save()
        
        return JsonResponse({'ok': True, 'mensaje': f'Alerta creada para {parada.name}'})
    
    paradas = Stop.objects.filter(is_active=True)
    rutas = Route.objects.filter(is_active=True)
    alertas = request.user.alertas.filter(activa=True)
    return render(request, 'notifications/alertas.html', {'paradas': paradas, 'rutas': rutas, 'alertas': alertas})

@login_required
def desactivar_alerta(request, pk):
    from .models import Alerta
    alerta = get_object_or_404(Alerta, pk=pk, usuario=request.user)
    alerta.activa = False
    alerta.save()
    return JsonResponse({'ok': True})
