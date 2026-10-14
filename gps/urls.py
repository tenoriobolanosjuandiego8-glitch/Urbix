from django.urls import path
from . import views

app_name = 'gps'

urlpatterns = [
    path('reportar/', views.report_location, name='report_location'),
]
