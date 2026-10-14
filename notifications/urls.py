from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('alertas/', views.crear_alerta, name='crear_alerta'),
    path('alertas/<int:pk>/desactivar/', views.desactivar_alerta, name='desactivar_alerta'),
    path('', views.notification_list, name='list'),
    path('<int:pk>/leida/', views.mark_read, name='mark_read'),
    path('todas-leidas/', views.mark_all_read, name='mark_all_read'),
    path('push/suscribir/', views.push_subscribe, name='push_subscribe'),
    path('push/desuscribir/', views.push_unsubscribe, name='push_unsubscribe'),
]
