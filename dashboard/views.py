"""
dashboard/views.py
Redirección según rol, paneles de usuario/conductor/administrador
con estadísticas, y páginas de error personalizadas.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from accounts.decorators import admin_required, driver_required
from accounts.models import DriverProfile
from buses.models import Bus
from routes.models import Route
from events.models import Event
from reports.models import Report, DriverShift

User = get_user_model()


def splash(request):
    """Pantalla de inicio pública (storyboard escena 1)."""
    if request.user.is_authenticated:
        return redirect('dashboard:redirect')
    return render(request, 'dashboard/index.html')


@login_required
def redirect_by_role(request):
    role = request.user.role
    if role == User.Role.ADMIN or request.user.is_superuser:
        return redirect('dashboard:admin')
    if role == User.Role.CONDUCTOR:
        return redirect('dashboard:driver')
    return redirect('dashboard:home')


@login_required
def home(request):
    """Pantalla principal del usuario (accesos rápidos + próximos eventos)."""
    from interactions.models import get_recommendations_for_user
    events = Event.objects.filter(is_active=True, start_at__gte=timezone.now())[:3]
    recommendations = get_recommendations_for_user(request.user)
    return render(request, 'dashboard/principal.html', {'events': events, 'recommendations': recommendations})


@driver_required
def driver_dashboard(request):
    profile = getattr(request.user, 'driver_profile', None)
    shifts_today = DriverShift.objects.filter(driver=request.user, started_at__date=timezone.now().date())
    return render(request, 'dashboard/dashboard-conductor.html', {
        'profile': profile, 'shifts_today': shifts_today,
    })


@admin_required
def admin_dashboard(request):
    stats = {
        'users_count': User.objects.filter(role=User.Role.USUARIO).count(),
        'drivers_count': DriverProfile.objects.count(),
        'drivers_active_now': DriverProfile.objects.filter(
            status='activo', assigned_bus__status=Bus.Status.EN_RUTA).count(),
        'buses_count': Bus.objects.filter(is_active=True).count(),
        'routes_count': Route.objects.filter(is_active=True).count(),
        'reports_open': Report.objects.filter(status=Report.Status.ABIERTO).count(),
        'operator': 'Transpubenza',
    }
    fleet_status = Bus.objects.values('status').annotate(total=Count('id'))
    recent_reports = Report.objects.select_related('driver')[:6]
    drivers = DriverProfile.objects.select_related('user', 'assigned_bus', 'assigned_route')[:10]
    return render(request, 'dashboard/dashboard-admin.html', {
        'stats': stats, 'fleet_status': fleet_status,
        'recent_reports': recent_reports, 'drivers': drivers,
    })


@admin_required
def admin_users_list(request):
    users = User.objects.filter(role=User.Role.USUARIO)
    rows = [{
        'cells': [u.get_full_name() or u.username, u.email, u.phone or '—', 'Activo' if u.is_active else 'Inactivo'],
        'toggle_url': reverse('dashboard:admin_user_toggle', args=[u.pk]),
    } for u in users]
    return render(request, 'partials/admin_list_generic.html', {
        'title': 'Usuarios registrados', 'headers': ['Nombre', 'Correo', 'Teléfono', 'Estado'], 'rows': rows,
    })


@admin_required
def admin_user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
    return redirect('dashboard:admin_users')


@admin_required
def admin_drivers_list(request):
    drivers = DriverProfile.objects.select_related('user', 'assigned_bus', 'assigned_route')
    rows = [{
        'cells': [d.user.get_full_name(), d.license_number, d.assigned_bus.code if d.assigned_bus else '—',
                  d.assigned_route.name if d.assigned_route else '—', d.get_status_display()],
    } for d in drivers]
    return render(request, 'partials/admin_list_generic.html', {
        'title': 'Conductores', 'headers': ['Nombre', 'Licencia', 'Bus asignado', 'Ruta asignada', 'Estado'], 'rows': rows,
    })


@admin_required
def stats_view(request):
    import json
    from django.contrib.contenttypes.models import ContentType
    from django.db.models.functions import ExtractHour
    from interactions.models import HistoryEntry
    from routes.models import Stop

    route_ct = ContentType.objects.get_for_model(Route)
    stop_ct = ContentType.objects.get_for_model(Stop)

    route_views = list(HistoryEntry.objects.filter(content_type=route_ct, kind=HistoryEntry.Kind.VIEW)
                        .values('object_id').annotate(total=Count('id')))
    route_map = {r.id: r for r in Route.objects.select_related('operator')
                 .filter(id__in=[x['object_id'] for x in route_views])}

    top_routes = sorted((
        {'name': route_map[x['object_id']].name, 'operator': (route_map[x['object_id']].operator.name if route_map[x['object_id']].operator else ''), 'total': x['total']}
        for x in route_views if x['object_id'] in route_map
    ), key=lambda r: -r['total'])[:8]

    operator_counts = {}
    for x in route_views:
        route = route_map.get(x['object_id'])
        if route and route.operator:
            operator_counts[route.operator.name] = operator_counts.get(route.operator.name, 0) + x['total']
    operator_stats = sorted(operator_counts.items(), key=lambda kv: -kv[1])

    stop_views = list(HistoryEntry.objects.filter(content_type=stop_ct, kind=HistoryEntry.Kind.VIEW)
                       .values('object_id').annotate(total=Count('id')).order_by('-total')[:8])
    stop_map = {s.id: s for s in Stop.objects.filter(id__in=[x['object_id'] for x in stop_views])}
    top_stops = [{'name': stop_map[x['object_id']].name, 'total': x['total']}
                 for x in stop_views if x['object_id'] in stop_map]

    hours = (HistoryEntry.objects.annotate(hour=ExtractHour('created_at'))
             .values('hour').annotate(total=Count('id')).order_by('hour'))
    hours_by_h = {h['hour']: h['total'] for h in hours}
    hours_labels = [f'{h}:00' for h in range(24)]
    hours_data = [hours_by_h.get(h, 0) for h in range(24)]

    context = {
        'top_routes': top_routes,
        'top_stops': top_stops,
        'operator_stats': operator_stats,
        'users_count': User.objects.filter(role=User.Role.USUARIO).count(),
        'has_data': bool(route_views or stop_views),
        'chart_top_routes_labels': json.dumps([r['name'] for r in top_routes]),
        'chart_top_routes_data': json.dumps([r['total'] for r in top_routes]),
        'chart_operator_labels': json.dumps([o[0] for o in operator_stats]),
        'chart_operator_data': json.dumps([o[1] for o in operator_stats]),
        'chart_hours_labels': json.dumps(hours_labels),
        'chart_hours_data': json.dumps(hours_data),
        'chart_stops_labels': json.dumps([s['name'] for s in top_stops]),
        'chart_stops_data': json.dumps([s['total'] for s in top_stops]),
    }
    return render(request, 'dashboard/estadisticas.html', context)


@login_required
def settings_view(request):
    return render(request, 'dashboard/configuracion.html')


@admin_required
def audit_log(request):
    from accounts.models import ActivityLog, LoginAttempt
    activity = ActivityLog.objects.select_related('user')[:100]
    logins = LoginAttempt.objects.all()[:50]
    failed_logins_24h = LoginAttempt.objects.filter(success=False).count()
    return render(request, 'dashboard/auditoria.html', {
        'activity': activity, 'logins': logins, 'failed_logins_24h': failed_logins_24h,
    })


def help_center(request):
    return render(request, 'dashboard/ayuda.html')


def changelog(request):
    return render(request, 'dashboard/changelog.html')


def privacy_policy(request):
    return render(request, 'dashboard/privacidad.html')


def terms_of_use(request):
    return render(request, 'dashboard/terminos.html')


def error_404(request, exception=None):
    return render(request, 'dashboard/404.html', status=404)


def error_500(request):
    return render(request, 'dashboard/500.html', status=500)


@admin_required
def admin_dashboard_mejorado(request):
    from buses.models import Bus
    from routes.models import Route
    from reports.models import Report, ReporteTrafico
    from notifications.models import Notification
    from django.utils import timezone
    from datetime import timedelta
    
    ahora = timezone.now()
    hoy = ahora.date()
    hace_1h = ahora - timedelta(hours=1)
    
    stats = {
        'buses_total': Bus.objects.filter(is_active=True).count(),
        'buses_en_ruta': Bus.objects.filter(is_active=True, status=Bus.Status.EN_RUTA).count(),
        'buses_con_retraso': Bus.objects.filter(is_active=True, status=Bus.Status.RETRASO).count(),
        'buses_mantenimiento': Bus.objects.filter(is_active=True, status=Bus.Status.MANTENIMIENTO).count(),
        'rutas_activas': Route.objects.filter(is_active=True).count(),
        'reportes_hoy': Report.objects.filter(created_at__date=hoy).count(),
        'reportes_trafico_activos': ReporteTrafico.objects.filter(activa=True, expira__gt=ahora).count(),
        'ocupacion_promedio': 'Media',  # Simplificado
    }
    
    buses_en_ruta = Bus.objects.filter(
        is_active=True, status=Bus.Status.EN_RUTA
    ).select_related('route', 'current_driver').values(
        'id', 'code', 'route__name', 'current_driver__user__first_name', 'last_speed_kmh'
    )[:10]
    
    reportes_recientes = Report.objects.filter(
        created_at__date=hoy
    ).select_related('driver', 'route').order_by('-created_at')[:8]
    
    rutas_mas_usadas = Route.objects.filter(is_active=True).annotate(
        bus_count=Count('buses')
    ).order_by('-bus_count')[:5]
    
    trafico_activo = ReporteTrafico.objects.filter(
        activa=True, expira__gt=ahora
    ).values('nivel').annotate(cantidad=Count('id'))
    
    return render(request, 'dashboard/admin_dashboard_mejorado.html', {
        'stats': stats,
        'buses_en_ruta': buses_en_ruta,
        'reportes_recientes': reportes_recientes,
        'rutas_mas_usadas': rutas_mas_usadas,
        'trafico_activo': trafico_activo,
    })
