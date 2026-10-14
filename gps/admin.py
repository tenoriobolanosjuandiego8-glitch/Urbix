from django.contrib import admin
from .models import GPSLocation


@admin.register(GPSLocation)
class GPSLocationAdmin(admin.ModelAdmin):
    list_display = ('bus', 'driver', 'latitude', 'longitude', 'speed_kmh', 'recorded_at')
    list_filter = ('bus',)
    date_hierarchy = 'recorded_at'
    readonly_fields = ('recorded_at',)
