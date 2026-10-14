from django.urls import path
from . import views

app_name = 'buses'

urlpatterns = [
    path('admin/', views.bus_admin_list, name='admin_list'),
    path('admin/nuevo/', views.bus_create, name='create'),
    path('admin/<int:pk>/editar/', views.bus_edit, name='edit'),
    path('admin/<int:pk>/eliminar/', views.bus_delete, name='delete'),
]
