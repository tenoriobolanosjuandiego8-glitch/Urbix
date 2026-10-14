"""
interactions/gamification.py
Sistema de puntos, nivel e insignias — calculado al vuelo a partir de
lo que el usuario ya hizo (favoritos, calificaciones, comentarios,
reportes, viajes planificados). No usa modelos ni señales nuevas: es
rápido, siempre exacto, y no puede desincronizarse.
"""
from django.contrib.contenttypes.models import ContentType

LEVELS = [
    (0, 'Explorador'),
    (20, 'Viajero frecuente'),
    (50, 'Local de Popayán'),
    (100, 'Experto en rutas'),
    (200, 'Embajador URBIX'),
    (400, 'Leyenda URBIX'),
]


def get_gamification_stats(user):
    from .models import Favorite, Rating, Comment, HistoryEntry

    favorites_count = Favorite.objects.filter(user=user).count()
    ratings_count = Rating.objects.filter(user=user).count()
    comments_count = Comment.objects.filter(user=user).count()
    trips_planned = HistoryEntry.objects.filter(user=user, kind=HistoryEntry.Kind.SEARCH,
                                                 detail__startswith='Viaje planeado').count()
    try:
        from reports.models import Report
        reports_count = Report.objects.filter(driver=user).count()
    except Exception:
        reports_count = 0

    points = favorites_count * 2 + ratings_count * 3 + comments_count * 2 + reports_count * 5 + trips_planned * 1

    level_name = LEVELS[0][1]
    next_threshold = LEVELS[1][0] if len(LEVELS) > 1 else None
    for i, (threshold, name) in enumerate(LEVELS):
        if points >= threshold:
            level_name = name
            next_threshold = LEVELS[i + 1][0] if i + 1 < len(LEVELS) else None

    progress_pct = 100
    if next_threshold:
        prev_threshold = max([t for t, _ in LEVELS if t <= points], default=0)
        span = next_threshold - prev_threshold
        progress_pct = int(((points - prev_threshold) / span) * 100) if span else 100

    badges = []
    if favorites_count >= 1:
        badges.append({'icon': 'bi-heart-fill', 'label': 'Primer favorito', 'earned': True})
    if favorites_count >= 10:
        badges.append({'icon': 'bi-collection-fill', 'label': 'Coleccionista', 'earned': True})
    if ratings_count >= 5:
        badges.append({'icon': 'bi-star-fill', 'label': 'Crítico activo', 'earned': True})
    if comments_count >= 5:
        badges.append({'icon': 'bi-chat-dots-fill', 'label': 'Voz de la comunidad', 'earned': True})
    if trips_planned >= 3:
        badges.append({'icon': 'bi-signpost-2-fill', 'label': 'Planificador experto', 'earned': True})
    if reports_count >= 1:
        badges.append({'icon': 'bi-flag-fill', 'label': 'Colaborador vial', 'earned': True})
    if points >= 100:
        badges.append({'icon': 'bi-trophy-fill', 'label': 'Embajador URBIX', 'earned': True})

    return {
        'points': points, 'level_name': level_name, 'next_threshold': next_threshold,
        'progress_pct': progress_pct, 'badges': badges,
        'stats': {
            'favorites': favorites_count, 'ratings': ratings_count,
            'comments': comments_count, 'reports': reports_count, 'trips_planned': trips_planned,
        },
    }
