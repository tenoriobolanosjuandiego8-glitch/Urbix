"""events/views.py"""
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from accounts.decorators import admin_required
from .models import Event
from .forms import EventForm


def event_list(request):
    events = Event.objects.filter(is_active=True, start_at__gte=timezone.now() - timezone.timedelta(days=1))
    return render(request, 'events/eventos.html', {'events': events})


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk, is_active=True)
    return render(request, 'events/detalle.html', {'event': event})


@admin_required
def event_admin_list(request):
    events = Event.objects.all()
    rows = [{
        'cells': [e.name, e.get_category_display(), e.place, e.start_at.strftime('%Y-%m-%d %H:%M'),
                  'Activo' if e.is_active else 'Inactivo'],
        'edit_url': reverse('events:edit', args=[e.pk]),
        'delete_url': reverse('events:delete', args=[e.pk]),
    } for e in events]
    return render(request, 'partials/admin_list_generic.html', {
        'title': 'Eventos', 'headers': ['Nombre', 'Categoría', 'Lugar', 'Fecha', 'Estado'],
        'rows': rows, 'create_url': reverse('events:create'),
    })


@admin_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento creado correctamente.')
            return redirect('events:admin_list')
    else:
        form = EventForm()
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': 'Nuevo evento', 'back_url': reverse('events:admin_list')})


@admin_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento actualizado correctamente.')
            return redirect('events:admin_list')
    else:
        form = EventForm(instance=event)
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': f'Editar {event.name}', 'back_url': reverse('events:admin_list')})


@admin_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        messages.info(request, 'Evento eliminado.')
    return redirect('events:admin_list')
