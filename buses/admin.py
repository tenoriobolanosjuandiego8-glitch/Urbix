from django.contrib import admin
from .models import Bus


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('code', 'plate', 'route', 'status', 'capacity', 'last_speed_kmh', 'is_active')
    list_filter = ('status', 'is_active', 'route__operator', 'route')
    search_fields = ('code', 'plate')
    list_editable = ('status',)
    autocomplete_fields = ('route',)
