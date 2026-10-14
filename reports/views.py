"""reports/views.py"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import driver_required, admin_required
from .models import Report, DriverShift
from .forms import ReportForm

# Tipos de reporte que ameritan avisar a los usuarios que siguen esa ruta
NOTIFY_WORTHY_KINDS = {
    Report.Kind.ACCIDENTE: ('bi-exclamation-octagon', 'Accidente reportado'),
    Report.Kind.CIERRE_VIA: ('bi-cone-striped', 'Cierre de vía'),
    Report.Kind.TRAFICO: ('bi-signpost-2', 'Tráfico pesado'),
    Report.Kind.BUS_LLENO: ('bi-people-fill', 'Bus lleno'),
}


def _notify_route_followers(report):
    """Crea una Notification (y push real si está activado) para cada
    usuario que tiene esta ruta en favoritos."""
    if not report.route or report.kind not in NOTIFY_WORTHY_KINDS:
        return
    icon, label = NOTIFY_WORTHY_KINDS[report.kind]

    from django.contrib.contenttypes.models import ContentType
    from interactions.models import Favorite
    from notifications.models import Notification
    from notifications.push import send_push_to_user

    route_ct = ContentType.objects.get_for_model(report.route)
    followers = Favorite.objects.filter(content_type=route_ct, object_id=report.route_id).select_related('user')

    for fav in followers:
        Notification.objects.create(
            user=fav.user, kind=Notification.Kind.INCIDENTE, icon=icon,
            title=f'{label} · {report.route.name}',
            body=report.description[:120],
        )
        send_push_to_user(fav.user, title=f'URBIX · {label}', body=f'{report.route.name}: {report.description[:100]}')


@driver_required
def report_create(request):
    driver_profile = getattr(request.user, 'driver_profile', None)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.driver = request.user
            report.bus = driver_profile.assigned_bus if driver_profile else None
            report.route = driver_profile.assigned_route if driver_profile else None
            report.save()
            _notify_route_followers(report)
            messages.success(request, 'Reporte enviado correctamente.')
            return redirect('dashboard:driver')
    else:
        form = ReportForm()
    return render(request, 'reports/form.html', {'form': form})


@driver_required
def shift_status_update(request):
    """Actualiza el estado del bus asignado al conductor (En ruta, Con retraso, etc.)."""
    driver_profile = getattr(request.user, 'driver_profile', None)
    if request.method == 'POST' and driver_profile and driver_profile.assigned_bus:
        status_map = {
            'En ruta': 'en_ruta', 'Con retraso': 'retraso',
            'En parada': 'en_ruta', 'Fuera de servicio': 'fuera_servicio',
        }
        bus = driver_profile.assigned_bus
        bus.status = status_map.get(request.POST.get('status'), bus.status)
        bus.save(update_fields=['status'])
        messages.success(request, 'Estado del servicio actualizado.')
    return redirect('dashboard:driver')


@admin_required
def report_admin_list(request):
    reports = Report.objects.select_related('driver', 'bus', 'route').all()
    status = request.GET.get('status')
    if status:
        reports = reports.filter(status=status)
    return render(request, 'reports/admin_list.html', {'reports': reports})


@admin_required
def report_update_status(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        report.status = request.POST.get('status', report.status)
        if report.status == Report.Status.RESUELTO and not report.resolved_at:
            report.resolved_at = timezone.now()
        report.save()
        messages.success(request, 'Reporte actualizado.')
    return redirect('reports:admin_list')


@driver_required
@require_POST
def crear_reporte_trafico(request):
    from .models import ReporteTrafico
    import json
    
    try:
        data = json.loads(request.body or '{}')
        perfil = request.user.driver_profile
        
        reporte = ReporteTrafico.objects.create(
            conductor=request.user,
            bus=perfil.assigned_bus,
            ubicacion_lat=float(data.get('lat')),
            ubicacion_lng=float(data.get('lng')),
            nivel=data.get('nivel', 'medio'),
            tipo=data.get('tipo', 'congestión'),
            descripcion=data.get('descripcion', '')
        )
        return JsonResponse({'ok': True, 'id': reporte.id})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

def mapa_reportes(request):
    from .models import ReporteTrafico
    from django.utils import timezone
    
    reportes = ReporteTrafico.objects.filter(
        activa=True,
        expira__gt=timezone.now()
    ).values('id', 'ubicacion_lat', 'ubicacion_lng', 'nivel', 'tipo', 'creada')
    
    return JsonResponse({'reportes': list(reportes)})

@login_required
def reportar_trafico(request):
    if request.user.role != 'conductor':
        from django.shortcuts import render
        return render(request, 'dashboard/error_403.html')
    return render(request, 'reports/reportar_trafico.html')
