"""routes/views.py"""
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from accounts.decorators import admin_required
from interactions.models import HistoryEntry
from .models import Route, ScheduleEntry, Stop, Operator, RouteStop, TripShare
from .forms import RouteForm, OperatorForm


def route_list(request):
    routes = Route.objects.filter(is_active=True).select_related('operator').prefetch_related('routestop_set__stop')
    operators = Operator.objects.filter(is_active=True)
    operator_filter = request.GET.get('empresa')
    if operator_filter:
        routes = routes.filter(operator_id=operator_filter)
    return render(request, 'routes/rutas.html', {
        'routes': routes, 'operators': operators, 'operator_filter': operator_filter,
    })


def route_detail(request, pk):
    route = get_object_or_404(
        Route.objects.select_related('operator'), pk=pk, is_active=True
    )
    stops = route.routestop_set.select_related('stop').order_by('order')
    if request.user.is_authenticated:
        from django.contrib.contenttypes.models import ContentType
        HistoryEntry.objects.create(
            user=request.user, kind=HistoryEntry.Kind.VIEW,
            content_type=ContentType.objects.get_for_model(route), object_id=route.pk,
            detail=f'Ruta: {route.name}',
        )
    return render(request, 'routes/detalle.html', {'route': route, 'stops': stops})


def schedule_list(request):
    routes = Route.objects.filter(is_active=True)
    selected_id = request.GET.get('ruta')
    selected = get_object_or_404(Route, pk=selected_id) if selected_id else routes.first()
    entries = selected.schedule_entries.all() if selected else []
    return render(request, 'routes/horarios.html', {
        'routes': routes, 'selected': selected, 'entries': entries,
    })


def stop_search(request):
    """
    Buscador de lugares (barrios, universidades, hospitales, parques...).
    Le permite al usuario ver qué rutas/buses pasan cerca de un lugar.
    """
    query = request.GET.get('q', '').strip()
    category = request.GET.get('categoria', '').strip()

    stops = Stop.objects.filter(is_active=True)
    if query:
        stops = stops.filter(name__icontains=query)
        if request.user.is_authenticated:
            HistoryEntry.objects.create(user=request.user, kind=HistoryEntry.Kind.SEARCH, detail=f'Búsqueda: {query}')
    if category:
        stops = stops.filter(category=category)

    return render(request, 'routes/paraderos.html', {
        'stops': stops[:60], 'query': query, 'category': category,
        'categories': Stop.Category.choices,
    })


def stop_detail(request, pk):
    stop = get_object_or_404(Stop, pk=pk, is_active=True)
    routes_here = stop.routes_here.select_related('operator')
    # ETA simulada para la demo (aún no hay GPS real conectado a paraderos):
    # determinista por parada + bloque de 5 min, así no cambia en cada refresh.
    rnd = random.Random(stop.id * 1000 + timezone.now().minute // 5)
    eta_by_route = {r.id: rnd.randint(2, 15) for r in routes_here}
    if request.user.is_authenticated:
        from django.contrib.contenttypes.models import ContentType
        HistoryEntry.objects.create(
            user=request.user, kind=HistoryEntry.Kind.VIEW,
            content_type=ContentType.objects.get_for_model(stop), object_id=stop.pk,
            detail=f'Paradero: {stop.name}',
        )
    return render(request, 'routes/parada_detalle.html', {
        'stop': stop, 'routes_here': routes_here, 'eta_by_route': eta_by_route,
    })


def operator_list(request):
    operators = Operator.objects.filter(is_active=True).annotate(routes_count=Count('routes'))
    return render(request, 'routes/empresas.html', {'operators': operators})


def operator_detail(request, pk):
    operator = get_object_or_404(Operator, pk=pk, is_active=True)
    routes = operator.routes.filter(is_active=True).prefetch_related('routestop_set__stop')
    from buses.models import Bus
    buses = Bus.objects.filter(route__operator=operator, is_active=True).select_related('route')
    return render(request, 'routes/empresa_detalle.html', {'operator': operator, 'routes': routes, 'buses': buses})


@login_required
def trip_share_create(request):
    """Genera un enlace temporal (4 horas) para compartir el viaje actual."""
    from datetime import timedelta
    from django.utils import timezone as tz

    route_id = request.POST.get('route_id') or request.GET.get('route_id')
    origin_id = request.GET.get('origen')
    dest_id = request.GET.get('destino')
    share = TripShare.objects.create(
        user=request.user,
        route_id=route_id or None,
        origin_stop_id=origin_id or None,
        destination_stop_id=dest_id or None,
        expires_at=tz.now() + timedelta(hours=4),
    )
    return redirect('routes:trip_share_view', token=share.token)


def trip_share_view(request, token):
    """Página pública (sin login) para que un contacto vea el viaje compartido."""
    share = get_object_or_404(TripShare, token=token)
    return render(request, 'routes/viaje_compartido.html', {'share': share})


def route_compare(request):
    """Comparador: elige hasta 3 rutas y las ve una junto a la otra."""
    ids = request.GET.getlist('ruta')
    routes = Route.objects.filter(pk__in=ids, is_active=True).select_related('operator').prefetch_related('routestop_set__stop')
    all_routes = Route.objects.filter(is_active=True).select_related('operator')
    return render(request, 'routes/comparador.html', {'routes': routes, 'all_routes': all_routes, 'selected_ids': [int(i) for i in ids]})


def trip_planner(request):
    """
    Planificador de viaje: el usuario elige un paradero de origen y uno de
    destino, y el sistema busca la mejor combinación de rutas (directa, o
    con un transbordo) entre las empresas reales de Popayán.
    """
    origin_id = request.GET.get('origen')
    dest_id = request.GET.get('destino')
    origin_stop = dest_stop = None
    results = []

    if origin_id and dest_id and origin_id != dest_id:
        origin_stop = get_object_or_404(Stop, pk=origin_id)
        dest_stop = get_object_or_404(Stop, pk=dest_id)

        direct_routes = (Route.objects.filter(is_active=True, routestop__stop=origin_stop)
                          .filter(routestop__stop=dest_stop).distinct().select_related('operator'))
        for route in direct_routes:
            rs_list = list(route.routestop_set.order_by('order'))
            order_map = {rs.stop_id: rs.order for rs in rs_list}
            if order_map.get(origin_stop.id, -1) < order_map.get(dest_stop.id, -2):
                total_span = (rs_list[-1].order - rs_list[0].order) or 1
                segment = order_map[dest_stop.id] - order_map[origin_stop.id]
                est_minutes = max(5, round(route.duration_minutes * segment / total_span))
                results.append({
                    'type': 'directo', 'transfers': 0, 'est_minutes': est_minutes,
                    'legs': [route], 'transfer_stop': None,
                })

        if not results:
            routes_from_origin = (Route.objects.filter(is_active=True, routestop__stop=origin_stop)
                                   .distinct().select_related('operator'))
            routes_to_dest = (Route.objects.filter(is_active=True, routestop__stop=dest_stop)
                               .distinct().select_related('operator'))
            seen = set()
            for r1 in routes_from_origin:
                r1_stops = list(r1.routestop_set.order_by('order'))
                r1_order = {rs.stop_id: rs.order for rs in r1_stops}
                if origin_stop.id not in r1_order:
                    continue
                downstream = {sid for sid, o in r1_order.items() if o > r1_order[origin_stop.id]}
                for r2 in routes_to_dest:
                    if r2.id == r1.id:
                        continue
                    r2_stops = list(r2.routestop_set.order_by('order'))
                    r2_order = {rs.stop_id: rs.order for rs in r2_stops}
                    if dest_stop.id not in r2_order:
                        continue
                    upstream = {sid for sid, o in r2_order.items() if o < r2_order[dest_stop.id]}
                    common = downstream & upstream
                    if not common:
                        continue
                    transfer_id = min(common, key=lambda sid: r1_order[sid])
                    key = (r1.id, r2.id, transfer_id)
                    if key in seen:
                        continue
                    seen.add(key)
                    transfer_stop = Stop.objects.get(pk=transfer_id)
                    span1 = (r1_stops[-1].order - r1_stops[0].order) or 1
                    seg1 = r1_order[transfer_id] - r1_order[origin_stop.id]
                    span2 = (r2_stops[-1].order - r2_stops[0].order) or 1
                    seg2 = r2_order[dest_stop.id] - r2_order[transfer_id]
                    est = max(8, round(r1.duration_minutes * seg1 / span1) + round(r2.duration_minutes * seg2 / span2) + 5)
                    results.append({
                        'type': 'transbordo', 'transfers': 1, 'est_minutes': est,
                        'legs': [r1, r2], 'transfer_stop': transfer_stop,
                    })

        results.sort(key=lambda r: (r['transfers'], r['est_minutes']))
        results = results[:6]

        if request.user.is_authenticated:
            HistoryEntry.objects.create(
                user=request.user, kind=HistoryEntry.Kind.SEARCH,
                detail=f'Viaje planeado: {origin_stop.name} → {dest_stop.name}',
            )

    stops = Stop.objects.filter(is_active=True).order_by('name')
    return render(request, 'routes/planificador.html', {
        'stops': stops, 'origin_stop': origin_stop, 'dest_stop': dest_stop, 'results': results,
    })


# ---------------- Administración (CRUD) ----------------
@admin_required
def route_admin_list(request):
    routes = Route.objects.select_related('operator').all()
    rows = [{
        'cells': [r.operator.name if r.operator else '—', r.code or '—', r.name,
                  f'{r.origin} - {r.destination}', r.duration_minutes,
                  'Activa' if r.is_active else 'Inactiva'],
        'edit_url': reverse('routes:edit', args=[r.pk]),
        'delete_url': reverse('routes:delete', args=[r.pk]),
        'toggle_url': reverse('routes:toggle_active', args=[r.pk]),
    } for r in routes]
    return render(request, 'partials/admin_list_generic.html', {
        'title': 'Rutas', 'headers': ['Empresa', 'Código', 'Nombre', 'Trayecto', 'Duración (min)', 'Estado'],
        'rows': rows, 'create_url': reverse('routes:create'),
    })


@admin_required
def route_create(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ruta creada correctamente.')
            return redirect('routes:admin_list')
    else:
        form = RouteForm()
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': 'Nueva ruta', 'back_url': reverse('routes:admin_list')})


@admin_required
def route_edit(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ruta actualizada correctamente.')
            return redirect('routes:admin_list')
    else:
        form = RouteForm(instance=route)
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': f'Editar {route.name}', 'back_url': reverse('routes:admin_list')})


@admin_required
def route_delete(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if request.method == 'POST':
        route.delete()
        messages.info(request, 'Ruta eliminada.')
    return redirect('routes:admin_list')


@admin_required
def route_toggle_active(request, pk):
    route = get_object_or_404(Route, pk=pk)
    route.is_active = not route.is_active
    route.save(update_fields=['is_active'])
    return redirect('routes:admin_list')


@admin_required
def operator_admin_list(request):
    operators = Operator.objects.annotate(routes_count=Count('routes'))
    rows = [{
        'cells': [o.name, o.brand_color, o.fleet_size, o.routes_count, 'Activa' if o.is_active else 'Inactiva'],
        'edit_url': reverse('routes:operator_edit', args=[o.pk]),
        'delete_url': reverse('routes:operator_delete', args=[o.pk]),
    } for o in operators]
    return render(request, 'partials/admin_list_generic.html', {
        'title': 'Empresas de transporte', 'headers': ['Nombre', 'Color', 'Flota (aprox.)', 'Rutas', 'Estado'],
        'rows': rows, 'create_url': reverse('routes:operator_create'),
    })


@admin_required
def operator_create(request):
    if request.method == 'POST':
        form = OperatorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa creada correctamente.')
            return redirect('routes:operator_admin_list')
    else:
        form = OperatorForm()
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': 'Nueva empresa', 'back_url': reverse('routes:operator_admin_list')})


@admin_required
def operator_edit(request, pk):
    operator = get_object_or_404(Operator, pk=pk)
    if request.method == 'POST':
        form = OperatorForm(request.POST, instance=operator)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa actualizada correctamente.')
            return redirect('routes:operator_admin_list')
    else:
        form = OperatorForm(instance=operator)
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': f'Editar {operator.name}', 'back_url': reverse('routes:operator_admin_list')})


@admin_required
def operator_delete(request, pk):
    operator = get_object_or_404(Operator, pk=pk)
    if request.method == 'POST':
        operator.delete()
        messages.info(request, 'Empresa eliminada.')
    return redirect('routes:operator_admin_list')
