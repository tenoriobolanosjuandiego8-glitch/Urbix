from django.urls import path
from . import views

app_name = 'tourism'

urlpatterns = [
    path('', views.place_list, name='list'),
    path('<int:pk>/', views.place_detail, name='detail'),

    path('admin/', views.place_admin_list, name='admin_list'),
    path('admin/nuevo/', views.place_create, name='create'),
    path('admin/<int:pk>/editar/', views.place_edit, name='edit'),
    path('admin/<int:pk>/eliminar/', views.place_delete, name='delete'),
]
