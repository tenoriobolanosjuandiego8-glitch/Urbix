"""
api/views.py
Endpoints REST de solo lectura para el contenido público (rutas,
buses, restaurantes, hoteles, turismo, eventos) y endpoints de
escritura autenticados para favoritos, comentarios y reporte de GPS.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from routes.models import Route
from buses.models import Bus
from gps.models import GPSLocation
from restaurants.models import Restaurant
from hotels.models import Hotel
from tourism.models import TouristPlace
from events.models import Event
from interactions.models import Favorite, Comment, toggle_favorite

from . import serializers as ser


class ReadOnlyOrAuth(permissions.IsAuthenticatedOrReadOnly):
    pass


class RouteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Route.objects.filter(is_active=True)
    serializer_class = ser.RouteSerializer
    permission_classes = [permissions.AllowAny]


class BusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bus.objects.filter(is_active=True)
    serializer_class = ser.BusSerializer
    permission_classes = [permissions.AllowAny]


class GPSLocationViewSet(viewsets.ModelViewSet):
    """Los conductores autenticados publican su posición (POST)."""
    queryset = GPSLocation.objects.all()
    serializer_class = ser.GPSLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post']

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user)


class RestaurantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Restaurant.objects.filter(is_active=True)
    serializer_class = ser.RestaurantSerializer
    permission_classes = [permissions.AllowAny]


class HotelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hotel.objects.filter(is_active=True)
    serializer_class = ser.HotelSerializer
    permission_classes = [permissions.AllowAny]


class TouristPlaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TouristPlace.objects.filter(is_active=True)
    serializer_class = ser.TouristPlaceSerializer
    permission_classes = [permissions.AllowAny]


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.filter(is_active=True)
    serializer_class = ser.EventSerializer
    permission_classes = [permissions.AllowAny]


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = ser.FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = ser.CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Comment.objects.all()
        ct = self.request.query_params.get('content_type')
        obj_id = self.request.query_params.get('object_id')
        if ct and obj_id:
            qs = qs.filter(content_type__model=ct, object_id=obj_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class URBIXAuthToken(ObtainAuthToken):
    """Login para la futura app móvil: retorna un token junto con el rol del usuario."""
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key, 'user_id': user.pk, 'email': user.email,
            'role': user.role, 'name': user.get_full_name(),
        })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def map_snapshot(request):
    """Foto completa del estado del mapa: rutas + última posición de cada bus."""
    routes = ser.RouteSerializer(Route.objects.filter(is_active=True), many=True).data
    buses = ser.BusSerializer(Bus.objects.filter(is_active=True), many=True).data
    return Response({'routes': routes, 'buses': buses})
