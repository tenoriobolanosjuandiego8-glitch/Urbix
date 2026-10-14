"""
business/views.py
Centro Empresarial URBIX.

Público: directorio y perfil de cada negocio (solo aprobados).
Empresa: registro, panel con estadísticas, promociones.
Administrador: cola de verificación (aprobar/rechazar/suspender) y
asignación manual de plan (mientras no hay pasarela de pago conectada).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from accounts.decorators import admin_required, business_required
from accounts.models import User
from interactions.models import HistoryEntry
from .models import Business, BusinessImage, BusinessPromotion, BusinessEvent, Subscription
from .forms import BusinessRegisterForm, BusinessEditForm, PromotionForm, BusinessRejectForm


# Público
def directory(request):
    qs = Business.objects.filter(status=Business.Status.APROBADO)

    business_type = request.GET.get('tipo', '').strip()
    query = request.GET.get('q', '').strip()
    if business_type:
        qs = qs.filter(business_type=business_type)
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if request.user.is_authenticated:
            HistoryEntry.objects.create(user=request.user, kind=HistoryEntry.Kind.SEARCH, detail=f'Negocios: {query}')

    # Premium primero, luego Destacado, luego Gratuito (solo si el plan no venció)
    qs = qs.annotate(
        plan_rank=Case(
            When(plan=Business.Plan.PREMIUM, plan_expires_at__gt=timezone.now(), then=Value(0)),
            When(plan=Business.Plan.DESTACADO, plan_expires_at__gt=timezone.now(), then=Value(1)),
            default=Value(2), output_field=IntegerField(),
        )
    ).order_by('plan_rank', '-created_at')

    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get('page'))

    # Registrar "apareció en una búsqueda" para los negocios visibles en esta página
    BusinessEvent.objects.bulk_create([
        BusinessEvent(business=b, kind=BusinessEvent.Kind.SEARCH_APPEARANCE) for b in page
    ])

    return render(request, 'business/directorio.html', {
        'businesses': page, 'types': Business.BusinessType.choices,
        'active_type': business_type, 'query': query,
    })


def business_detail(request, pk):
    business = get_object_or_404(Business, pk=pk)
    is_owner = request.user.is_authenticated and business.owner_id == request.user.id
    is_admin = request.user.is_authenticated and (request.user.is_urbix_admin)
    if not business.is_public and not is_owner and not is_admin:
        raise Http404('Este negocio aún no está disponible públicamente.')

    business.register_event(BusinessEvent.Kind.VIEW)
    promotions = business.promotions.filter(is_active=True)
    return render(request, 'business/detalle.html', {
        'business': business, 'promotions': promotions, 'is_owner': is_owner,
    })


def business_click(request, pk, channel):
    """Redirección con registro de clic, para medir interés real (llamar/whatsapp/web)."""
    business = get_object_or_404(Business, pk=pk, status=Business.Status.APROBADO)
    business.register_event(BusinessEvent.Kind.CLICK)
    urls = {
        'phone': f'tel:{business.phone}',
        'whatsapp': f'https://wa.me/{"".join(filter(str.isdigit, business.whatsapp or business.phone))}',
        'website': business.website,
        'instagram': f'https://instagram.com/{business.instagram.lstrip("@")}',
        'facebook': business.facebook if business.facebook.startswith('http') else f'https://facebook.com/{business.facebook}',
    }
    target = urls.get(channel)
    if not target:
        raise Http404
    return redirect(target)


# Empresa (dueño del negocio)
@login_required
def business_register(request):
    existing = Business.objects.filter(owner=request.user)
    if request.method == 'POST':
        form = BusinessRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            business.owner = request.user
            business.save()
            if request.user.role == User.Role.USUARIO:
                request.user.role = User.Role.EMPRESA
                request.user.save(update_fields=['role'])
            messages.success(
                request,
                '¡Negocio registrado! Quedó en estado "Pendiente de verificación" — '
                'nuestro equipo lo revisará antes de publicarlo.',
            )
            return redirect('business:dashboard')
    else:
        form = BusinessRegisterForm()
    return render(request, 'business/registro.html', {'form': form, 'existing': existing})


@business_required
def business_dashboard(request):
    business = Business.objects.filter(owner=request.user).first()
    if not business:
        return redirect('business:register')

    events = business.events.all()
    stats = {
        'views': events.filter(kind=BusinessEvent.Kind.VIEW).count(),
        'clicks': events.filter(kind=BusinessEvent.Kind.CLICK).count(),
        'search_appearances': events.filter(kind=BusinessEvent.Kind.SEARCH_APPEARANCE).count(),
    }
    ct = ContentType.objects.get_for_model(Business)
    from interactions.models import Comment, average_rating
    reviews = Comment.objects.filter(content_type=ct, object_id=business.pk, parent__isnull=True).select_related('user')
    avg = average_rating(business)

    return render(request, 'business/panel.html', {
        'business': business, 'stats': stats, 'reviews': reviews, 'avg_rating': avg,
        'promotions': business.promotions.all(),
        'subscriptions': business.subscriptions.all()[:5],
    })


@business_required
def business_edit(request, pk):
    business = get_object_or_404(Business, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = BusinessEditForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil del negocio actualizado.')
            return redirect('business:dashboard')
    else:
        form = BusinessEditForm(instance=business)
    return render(request, 'business/editar.html', {'form': form, 'business': business})


@business_required
def promotion_create(request):
    business = get_object_or_404(Business, owner=request.user)
    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            promo = form.save(commit=False)
            promo.business = business
            promo.save()
            messages.success(request, 'Promoción creada.')
            return redirect('business:dashboard')
    else:
        form = PromotionForm()
    return render(request, 'business/promocion_form.html', {'form': form})


@business_required
def promotion_delete(request, pk):
    promo = get_object_or_404(BusinessPromotion, pk=pk, business__owner=request.user)
    if request.method == 'POST':
        promo.delete()
        messages.info(request, 'Promoción eliminada.')
    return redirect('business:dashboard')


# Administrador: verificación y planes
@admin_required
def business_admin_list(request):
    status = request.GET.get('estado', '')
    qs = Business.objects.select_related('owner').all()
    if status:
        qs = qs.filter(status=status)
    return render(request, 'business/admin_list.html', {
        'businesses': qs, 'status_filter': status, 'statuses': Business.Status.choices,
        'pending_count': Business.objects.filter(status=Business.Status.PENDIENTE).count(),
    })


@admin_required
def business_approve(request, pk):
    business = get_object_or_404(Business, pk=pk)
    if request.method == 'POST':
        business.status = Business.Status.APROBADO
        business.verified_at = timezone.now()
        business.verified_by = request.user
        business.rejection_reason = ''
        business.save()
        messages.success(request, f'{business.name} fue aprobado y ya es visible públicamente.')
    return redirect('business:admin_list')


@admin_required
def business_reject(request, pk):
    business = get_object_or_404(Business, pk=pk)
    if request.method == 'POST':
        form = BusinessRejectForm(request.POST)
        if form.is_valid():
            business.status = Business.Status.RECHAZADO
            business.rejection_reason = form.cleaned_data['reason']
            business.save()
            messages.info(request, f'{business.name} fue rechazado.')
            return redirect('business:admin_list')
    else:
        form = BusinessRejectForm()
    return render(request, 'business/admin_reject_form.html', {'form': form, 'business': business})


@admin_required
def business_suspend(request, pk):
    business = get_object_or_404(Business, pk=pk)
    if request.method == 'POST':
        business.status = (Business.Status.SUSPENDIDO if business.status != Business.Status.SUSPENDIDO
                            else Business.Status.APROBADO)
        business.save()
        messages.info(request, f'Estado de {business.name} actualizado a {business.get_status_display()}.')
    return redirect('business:admin_list')


@admin_required
def business_set_plan(request, pk):
    """
    Asigna manualmente un plan mientras no hay pasarela de pago conectada.
    Crea igual un registro de Subscription (provider=manual) para dejar
    la contabilidad lista para cuando se conecte Wompi/Mercado Pago/etc.
    """
    business = get_object_or_404(Business, pk=pk)
    if request.method == 'POST':
        from datetime import timedelta
        plan = request.POST.get('plan')
        days = int(request.POST.get('days', 30))
        if plan in Business.Plan.values:
            business.plan = plan
            business.plan_expires_at = timezone.now() + timedelta(days=days) if plan != Business.Plan.GRATUITO else None
            business.save()
            Subscription.objects.create(
                business=business, plan=plan, provider=Subscription.Provider.MANUAL,
                status=Subscription.PaymentStatus.COMPLETADO, paid_at=timezone.now(),
            )
            messages.success(request, f'Plan de {business.name} actualizado a {business.get_plan_display()}.')
    return redirect('business:admin_list')
