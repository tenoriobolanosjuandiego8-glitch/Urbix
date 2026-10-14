from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('registro/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar/', views.recover_password_view, name='recover_password'),
    path('reset/<uidb64>/<token>/', views.reset_password_confirm_view, name='reset_password_confirm'),
    path('verificar/<uidb64>/<token>/', views.verify_email_view, name='verify_email'),
    path('perfil/', views.profile_view, name='profile'),
    path('cambiar-password/', views.change_password_view, name='change_password'),
    path('contactos-emergencia/', views.emergency_contacts_view, name='emergency_contacts'),
    path('contactos-emergencia/<int:pk>/eliminar/', views.emergency_contact_delete, name='emergency_contact_delete'),
    path('sos/', views.sos_view, name='sos'),
]
