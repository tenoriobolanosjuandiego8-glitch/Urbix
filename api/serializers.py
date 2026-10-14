"""
api/serializers.py
Serializadores REST para rutas, buses, paraderos, restaurantes,
hoteles, turismo, eventos y favoritos. Pensados para alimentar una
futura app móvil (Android/iOS) sin tocar el backend.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from routes.models import Route, Stop, ScheduleEntry
from buses.models import Bus
from gps.models import GPSLocation
from restaurants.models import Restaurant
from hotels.models import Hotel
from tourism.models import TouristPlace
from events.models import Event
from interactions.models import Favorite, Comment, average_rating

User = get_user_model()


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = ['id', 'name', 'latitude', 'longitude', 'address', 'is_active']


class ScheduleEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        fields = ['id', 'day_type', 'departure_time', 'frequency_minutes']


class RouteSerializer(serializers.ModelSerializer):
    path = serializers.ListField(source='path_coordinates', read_only=True)
    schedule_entries = ScheduleEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ['id', 'name', 'origin', 'destination', 'description', 'color',
                  'duration_minutes', 'distance_km', 'is_active', 'path', 'schedule_entries']


class BusSerializer(serializers.ModelSerializer):
    route_name = serializers.CharField(source='route.name', read_only=True)
    last_lat = serializers.SerializerMethodField()
    last_lng = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = ['id', 'code', 'plate', 'capacity', 'route', 'route_name',
                  'status', 'last_speed_kmh', 'last_lat', 'last_lng']

    def get_last_lat(self, obj):
        pos = obj.last_position
        return pos.latitude if pos else None

    def get_last_lng(self, obj):
        pos = obj.last_position
        return pos.longitude if pos else None


class GPSLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSLocation
        fields = ['id', 'bus', 'latitude', 'longitude', 'speed_kmh', 'heading', 'recorded_at']
        read_only_fields = ['recorded_at']


class RestaurantSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'tag', 'description', 'address', 'latitude', 'longitude',
                  'price_range', 'phone', 'opening_hours', 'cover_image', 'rating']

    def get_rating(self, obj):
        return average_rating(obj)


class HotelSerializer(serializers.ModelSerializer):
    services_list = serializers.ListField(read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'description', 'address', 'latitude', 'longitude',
                  'approx_price', 'services_list', 'phone', 'cover_image', 'rating']

    def get_rating(self, obj):
        return average_rating(obj)


class TouristPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TouristPlace
        fields = ['id', 'name', 'tag', 'history', 'curiosities', 'latitude', 'longitude', 'cover_image']


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'category', 'description', 'place', 'latitude', 'longitude',
                  'start_at', 'end_at', 'cover_image']


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'user_name', 'body', 'parent', 'created_at', 'is_edited']
        read_only_fields = ['user', 'created_at', 'is_edited']


class FavoriteSerializer(serializers.ModelSerializer):
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'content_type', 'content_type_name', 'object_id', 'created_at']
        read_only_fields = ['created_at']
