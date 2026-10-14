from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    path('', views.route_list, name='list'),
    path('horarios/', views.schedule_list, name='schedules'),
    path('paraderos/', views.stop_search, name='stops'),
    path('paraderos/<int:pk>/', views.stop_detail, name='stop_detail'),
    path('empresas/', views.operator_list, name='operators'),
    path('empresas/<int:pk>/', views.operator_detail, name='operator_detail'),
    path('planificador/', views.trip_planner, name='planner'),
    path('comparar/', views.route_compare, name='compare'),
    path('compartir-viaje/', views.trip_share_create, name='trip_share_create'),
    path('viaje/<uuid:token>/', views.trip_share_view, name='trip_share_view'),

    path('admin/', views.route_admin_list, name='admin_list'),
    path('admin/nueva/', views.route_create, name='create'),
    path('admin/<int:pk>/editar/', views.route_edit, name='edit'),
    path('admin/<int:pk>/eliminar/', views.route_delete, name='delete'),
    path('admin/<int:pk>/activar/', views.route_toggle_active, name='toggle_active'),

    path('admin/empresas/', views.operator_admin_list, name='operator_admin_list'),
    path('admin/empresas/nueva/', views.operator_create, name='operator_create'),
    path('admin/empresas/<int:pk>/editar/', views.operator_edit, name='operator_edit'),
    path('admin/empresas/<int:pk>/eliminar/', views.operator_delete, name='operator_delete'),

    path('<int:pk>/', views.route_detail, name='detail'),
]
