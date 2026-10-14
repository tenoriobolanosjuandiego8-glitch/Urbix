from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    path('', views.restaurant_list, name='list'),
    path('<int:pk>/', views.restaurant_detail, name='detail'),

    path('admin/', views.restaurant_admin_list, name='admin_list'),
    path('admin/nuevo/', views.restaurant_create, name='create'),
    path('admin/<int:pk>/editar/', views.restaurant_edit, name='edit'),
    path('admin/<int:pk>/eliminar/', views.restaurant_delete, name='delete'),
]
