from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.redirect_by_role, name='redirect'),
    path('inicio/', views.home, name='home'),
    path('conductor/', views.driver_dashboard, name='driver'),
    path('administrador/', views.admin_dashboard, name='admin'),
    path('administrador/usuarios/', views.admin_users_list, name='admin_users'),
    path('administrador/usuarios/<int:pk>/activar/', views.admin_user_toggle_active, name='admin_user_toggle'),
    path('administrador/conductores/', views.admin_drivers_list, name='admin_drivers'),
    path('administrador/estadisticas/', views.stats_view, name='stats'),
    path('administrador/auditoria/', views.audit_log, name='audit_log'),
    path('ayuda/', views.help_center, name='help'),
    path('configuracion/', views.settings_view, name='settings'),
    path('novedades/', views.changelog, name='changelog'),
    path('privacidad/', views.privacy_policy, name='privacy'),
    path('terminos/', views.terms_of_use, name='terms'),
]
