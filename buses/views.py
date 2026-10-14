"""buses/views.py"""
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from accounts.decorators import admin_required
from .models import Bus
from .forms import BusForm


@admin_required
def bus_admin_list(request):
    buses = Bus.objects.select_related('route').all()
    rows = [{
        'cells': [b.code, b.plate, b.operator_name, b.route.name if b.route else '—', b.get_status_display(), b.capacity],
        'edit_url': reverse('buses:edit', args=[b.pk]),
        'delete_url': reverse('buses:delete', args=[b.pk]),
    } for b in buses]
    return render(request, 'partials/admin_list_generic.html', {
        'title': 'Buses', 'headers': ['Código', 'Placa', 'Empresa', 'Ruta', 'Estado', 'Capacidad'],
        'rows': rows, 'create_url': reverse('buses:create'),
    })


@admin_required
def bus_create(request):
    if request.method == 'POST':
        form = BusForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bus creado correctamente.')
            return redirect('buses:admin_list')
    else:
        form = BusForm()
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': 'Nuevo bus', 'back_url': reverse('buses:admin_list')})


@admin_required
def bus_edit(request, pk):
    bus = get_object_or_404(Bus, pk=pk)
    if request.method == 'POST':
        form = BusForm(request.POST, instance=bus)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bus actualizado correctamente.')
            return redirect('buses:admin_list')
    else:
        form = BusForm(instance=bus)
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': f'Editar {bus.code}', 'back_url': reverse('buses:admin_list')})


@admin_required
def bus_delete(request, pk):
    bus = get_object_or_404(Bus, pk=pk)
    if request.method == 'POST':
        bus.delete()
        messages.info(request, 'Bus eliminado.')
    return redirect('buses:admin_list')
