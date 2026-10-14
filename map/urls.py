from django.urls import path
from . import views
from . import nearby

app_name = 'map'

urlpatterns = [
    path('', views.map_page, name='page'),
    path('conductor/', views.mapaconductor, name='conductor'),
    path('datos.json', views.map_data, name='data'),
    path('cercanos.json', nearby.nearby_places, name='nearby'),
]
