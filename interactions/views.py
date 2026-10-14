"""
interactions/views.py
Vistas genéricas reutilizadas por restaurantes, hoteles, eventos,
lugares turísticos y rutas: alternar favorito, comentar (crear/editar/
eliminar/responder) y calificar. Se identifican por
`app_label`, `model` y `pk` en la URL, así no se repite la lógica en
cada app de contenido.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Favorite, Comment, Rating, HistoryEntry, toggle_favorite


def _get_object(app_label, model, pk):
    ct = get_object_or_404(ContentType, app_label=app_label, model=model)
    obj = get_object_or_404(ct.model_class(), pk=pk)
    return ct, obj


@login_required
@require_POST
def favorite_toggle(request, app_label, model, pk):
    ct, obj = _get_object(app_label, model, pk)
    is_fav = toggle_favorite(request.user, obj)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': is_fav})
    messages.success(request, 'Agregado a favoritos.' if is_fav else 'Eliminado de favoritos.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def history_list(request):
    entries = HistoryEntry.objects.filter(user=request.user).select_related('content_type')[:60]
    return render(request, 'interactions/historial.html', {'entries': entries})
    ct, obj = _get_object(app_label, model, pk)
    is_fav = toggle_favorite(request.user, obj)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': is_fav})
    messages.success(request, 'Agregado a favoritos.' if is_fav else 'Eliminado de favoritos.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('content_type')
    return render(request, 'interactions/favoritos.html', {'favorites': favorites})


@login_required
@require_POST
def comment_create(request, app_label, model, pk):
    ct, obj = _get_object(app_label, model, pk)
    body = request.POST.get('body', '').strip()
    parent_id = request.POST.get('parent_id')
    if body:
        comment = Comment.objects.create(
            user=request.user, content_type=ct, object_id=obj.pk,
            body=body[:1000], parent_id=parent_id or None,
        )
        HistoryEntry.objects.create(user=request.user, kind=HistoryEntry.Kind.COMMENT, content_type=ct, object_id=obj.pk)
        messages.success(request, 'Comentario publicado.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def comment_edit(request, pk):
    comment = get_object_or_404(Comment, pk=pk, user=request.user)
    body = request.POST.get('body', '').strip()
    if body:
        comment.body = body[:1000]
        comment.is_edited = True
        comment.save(update_fields=['body', 'is_edited', 'updated_at'])
        messages.success(request, 'Comentario actualizado.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk, user=request.user)
    comment.delete()
    messages.info(request, 'Comentario eliminado.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def flag_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    reason = request.POST.get('reason', 'otro')
    note = request.POST.get('note', '').strip()
    from .models import ContentFlag
    _, created = ContentFlag.objects.get_or_create(
        comment=comment, reported_by=request.user, defaults={'reason': reason, 'note': note[:300]},
    )
    if created:
        messages.success(request, 'Gracias, revisaremos este contenido.')
    else:
        messages.info(request, 'Ya habías denunciado este contenido.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def rate_object(request, app_label, model, pk):
    ct, obj = _get_object(app_label, model, pk)
    try:
        score = max(1, min(5, int(request.POST.get('score', 0))))
    except ValueError:
        score = 0
    if score:
        Rating.objects.update_or_create(
            user=request.user, content_type=ct, object_id=obj.pk,
            defaults={'score': score},
        )
        messages.success(request, '¡Gracias por tu calificación!')
    return redirect(request.META.get('HTTP_REFERER', '/'))
