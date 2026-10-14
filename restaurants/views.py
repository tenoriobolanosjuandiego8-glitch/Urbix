"""restaurants/views.py"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings

from accounts.decorators import admin_required
from interactions.models import HistoryEntry
from .models import Restaurant
from .forms import RestaurantForm


def restaurant_list(request):
    qs = Restaurant.objects.filter(is_active=True)
    query = request.GET.get('q', '').strip()
    tag = request.GET.get('tag', '').strip()
    if query:
        qs = qs.filter(name__icontains=query)
    if tag and tag != 'todos':
        qs = qs.filter(tag=tag)

    paginator = Paginator(qs, settings.URBIX_PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))
    tags = Restaurant.objects.filter(is_active=True).values_list('tag', flat=True).distinct()
    return render(request, 'restaurants/restaurantes.html', {
        'restaurants': page, 'tags': tags, 'query': query, 'active_tag': tag or 'todos',
    })


def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk, is_active=True)
    if request.user.is_authenticated:
        from django.contrib.contenttypes.models import ContentType
        HistoryEntry.objects.create(
            user=request.user, kind=HistoryEntry.Kind.VIEW,
            content_type=ContentType.objects.get_for_model(restaurant), object_id=restaurant.pk,
        )
    return render(request, 'restaurants/detalle.html', {'restaurant': restaurant})


# ---------------- Administración (CRUD) ----------------
@admin_required
def restaurant_admin_list(request):
    restaurants = Restaurant.objects.all()
    rows = [{
        'cells': [r.name, r.tag, r.price_range, r.address, 'Activo' if r.is_active else 'Inactivo'],
        'edit_url': reverse('restaurants:edit', args=[r.pk]),
        'delete_url': reverse('restaurants:delete', args=[r.pk]),
    } for r in restaurants]
    return render(request, 'partials/admin_list_generic.html', {
        'title': 'Restaurantes', 'headers': ['Nombre', 'Categoría', 'Precio', 'Dirección', 'Estado'],
        'rows': rows, 'create_url': reverse('restaurants:create'),
    })


@admin_required
def restaurant_create(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Restaurante creado correctamente.')
            return redirect('restaurants:admin_list')
    else:
        form = RestaurantForm()
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': 'Nuevo restaurante', 'back_url': reverse('restaurants:admin_list')})


@admin_required
def restaurant_edit(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Restaurante actualizado correctamente.')
            return redirect('restaurants:admin_list')
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, 'partials/admin_form_generic.html', {'form': form, 'title': f'Editar {restaurant.name}', 'back_url': reverse('restaurants:admin_list')})


@admin_required
def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        restaurant.delete()
        messages.info(request, 'Restaurante eliminado.')
    return redirect('restaurants:admin_list')
