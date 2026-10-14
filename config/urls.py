"""
URLs raíz del proyecto URBIX.
Cada app expone su propio urls.py; aquí solo se incluyen con su namespace.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

admin.site.site_header = 'URBIX · Panel de administración'
admin.site.site_title = 'URBIX Admin'
admin.site.index_title = 'Movilidad Inteligente en Popayán'

urlpatterns = [
    path('admin/', admin.site.urls),

    # Página de inicio (splash) y utilidades raíz
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='service_worker'),
    path('', include('dashboard.urls_root')),

    path('cuenta/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('mapa/', include('map.urls')),
    path('rutas/', include('routes.urls')),
    path('buses/', include('buses.urls')),
    path('gps/', include('gps.urls')),
    path('restaurantes/', include('restaurants.urls')),
    path('hoteles/', include('hotels.urls')),
    path('turismo/', include('tourism.urls')),
    path('eventos/', include('events.urls')),
    path('notificaciones/', include('notifications.urls')),
    path('reportes/', include('reports.urls')),
    path('interacciones/', include('interactions.urls')),
    path('asistente/', include('assistant.urls')),
    path('empresas-urbix/', include('business.urls')),

    # API REST (JSON) — pensada para una futura app móvil
    path('api/v1/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Páginas de error personalizadas
handler404 = 'dashboard.views.error_404'
handler500 = 'dashboard.views.error_500'
