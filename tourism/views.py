"""tourism/views.py"""
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from accounts.decorators import admin_required
from .models import TouristPlace
from .forms import TouristPlaceForm


def place_list(request):
    places = TouristPlace.objects.filter(is_active=True)
    return render(request, 'tourism/turismo.html', {'places': places})


def place_detail(request, pk):
    place = get_object_or_404(TouristPlace, pk=pk, is_active=True)
    return render(request, 'tourism/detalle.html', {'place': place})


@admin_required
def place_admin_list(request):
    places = TouristPlace.objects.all()
    rows = [{
        'cells': [p.name, p.tag, 'Activo' if p.is_active else 'Inactivo'],
        'edit_url': reverse('tourism:edit', args=[p.pk]),
        'delete_url': reverse('tourism:delete', args=[p.pk]),
    } for p in places]
    return render(request, 'partials/admin_list_generic.html', {
        'title': 'Lugares turísticos', 'headers': ['Nombre', 'Categoría', 'Estado'],
        'rows': rows, 'create_url': reverse('tourism:create'),
    })


@admin_required
def place_create(request):
    if request.method == 'POST':
        form = TouristPlaceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lugar turístico creado correctamente.')
            return redirect('tourism:admin_list')
    else:
        form = TouristPlaceForm()
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': 'Nuevo lugar turístico', 'back_url': reverse('tourism:admin_list')})


@admin_required
def place_edit(request, pk):
    place = get_object_or_404(TouristPlace, pk=pk)
    if request.method == 'POST':
        form = TouristPlaceForm(request.POST, request.FILES, instance=place)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lugar turístico actualizado correctamente.')
            return redirect('tourism:admin_list')
    else:
        form = TouristPlaceForm(instance=place)
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': f'Editar {place.name}', 'back_url': reverse('tourism:admin_list')})


@admin_required
def place_delete(request, pk):
    place = get_object_or_404(TouristPlace, pk=pk)
    if request.method == 'POST':
        place.delete()
        messages.info(request, 'Lugar turístico eliminado.')
    return redirect('tourism:admin_list')
