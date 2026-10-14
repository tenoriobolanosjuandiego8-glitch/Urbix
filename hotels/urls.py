from django.urls import path
from . import views

app_name = 'hotels'

urlpatterns = [
    path('', views.hotel_list, name='list'),
    path('<int:pk>/', views.hotel_detail, name='detail'),

    path('admin/', views.hotel_admin_list, name='admin_list'),
    path('admin/nuevo/', views.hotel_create, name='create'),
    path('admin/<int:pk>/editar/', views.hotel_edit, name='edit'),
    path('admin/<int:pk>/eliminar/', views.hotel_delete, name='delete'),
]
