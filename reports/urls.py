from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('trafico/crear/', views.crear_reporte_trafico, name='crear_trafico'),
    path('trafico/mapa/', views.mapa_reportes, name='mapa_reportes'),
    path('nuevo/', views.report_create, name='create'),
    path('estado/', views.shift_status_update, name='shift_status_update'),

    path('admin/', views.report_admin_list, name='admin_list'),
    path('admin/<int:pk>/estado/', views.report_update_status, name='update_status'),
]
