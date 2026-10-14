from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('rutas', views.RouteViewSet, basename='api-routes')
router.register('buses', views.BusViewSet, basename='api-buses')
router.register('gps', views.GPSLocationViewSet, basename='api-gps')
router.register('restaurantes', views.RestaurantViewSet, basename='api-restaurants')
router.register('hoteles', views.HotelViewSet, basename='api-hotels')
router.register('turismo', views.TouristPlaceViewSet, basename='api-tourism')
router.register('eventos', views.EventViewSet, basename='api-events')
router.register('favoritos', views.FavoriteViewSet, basename='api-favorites')
router.register('comentarios', views.CommentViewSet, basename='api-comments')

urlpatterns = [
    path('auth/token/', views.URBIXAuthToken.as_view(), name='api-token'),
    path('mapa/', views.map_snapshot, name='api-map-snapshot'),
    path('', include(router.urls)),
]
