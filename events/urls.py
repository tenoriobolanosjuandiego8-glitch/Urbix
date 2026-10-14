from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('<int:pk>/', views.event_detail, name='detail'),

    path('admin/', views.event_admin_list, name='admin_list'),
    path('admin/nuevo/', views.event_create, name='create'),
    path('admin/<int:pk>/editar/', views.event_edit, name='edit'),
    path('admin/<int:pk>/eliminar/', views.event_delete, name='delete'),
]
