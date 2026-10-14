from django.urls import path
from . import views

app_name = 'business'

urlpatterns = [
    path('', views.directory, name='directory'),
    path('registro/', views.business_register, name='register'),
    path('panel/', views.business_dashboard, name='dashboard'),
    path('panel/promocion/nueva/', views.promotion_create, name='promotion_create'),
    path('panel/promocion/<int:pk>/eliminar/', views.promotion_delete, name='promotion_delete'),
    path('<int:pk>/', views.business_detail, name='detail'),
    path('<int:pk>/editar/', views.business_edit, name='edit'),
    path('<int:pk>/ir/<str:channel>/', views.business_click, name='click'),

    path('admin/', views.business_admin_list, name='admin_list'),
    path('admin/<int:pk>/aprobar/', views.business_approve, name='approve'),
    path('admin/<int:pk>/rechazar/', views.business_reject, name='reject'),
    path('admin/<int:pk>/suspender/', views.business_suspend, name='suspend'),
    path('admin/<int:pk>/plan/', views.business_set_plan, name='set_plan'),
]
