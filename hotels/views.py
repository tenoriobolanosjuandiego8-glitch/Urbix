"""hotels/views.py"""
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from accounts.decorators import admin_required
from .models import Hotel
from .forms import HotelForm


def hotel_list(request):
    qs = Hotel.objects.filter(is_active=True)
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(name__icontains=query)
    paginator = Paginator(qs, settings.URBIX_PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'hotels/hoteles.html', {'hotels': page, 'query': query})


def hotel_detail(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk, is_active=True)
    return render(request, 'hotels/detalle.html', {'hotel': hotel})


@admin_required
def hotel_admin_list(request):
    hotels = Hotel.objects.all()
    rows = [{
        'cells': [h.name, f'${h.approx_price:,.0f}', h.address, 'Activo' if h.is_active else 'Inactivo'],
        'edit_url': reverse('hotels:edit', args=[h.pk]),
        'delete_url': reverse('hotels:delete', args=[h.pk]),
    } for h in hotels]
    return render(request, 'partials/admin_list_generic.html', {
        'title': 'Hoteles', 'headers': ['Nombre', 'Precio aprox.', 'Dirección', 'Estado'],
        'rows': rows, 'create_url': reverse('hotels:create'),
    })


@admin_required
def hotel_create(request):
    if request.method == 'POST':
        form = HotelForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hotel creado correctamente.')
            return redirect('hotels:admin_list')
    else:
        form = HotelForm()
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': 'Nuevo hotel', 'back_url': reverse('hotels:admin_list')})


@admin_required
def hotel_edit(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'POST':
        form = HotelForm(request.POST, request.FILES, instance=hotel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hotel actualizado correctamente.')
            return redirect('hotels:admin_list')
    else:
        form = HotelForm(instance=hotel)
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': f'Editar {hotel.name}', 'back_url': reverse('hotels:admin_list')})


@admin_required
def hotel_delete(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'POST':
        hotel.delete()
        messages.info(request, 'Hotel eliminado.')
    return redirect('hotels:admin_list')
