from django.contrib import admin
from .models import Route, Stop, RouteStop, ScheduleEntry, Operator


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand_color', 'fleet_size', 'phone', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    autocomplete_fields = ['stop']


class ScheduleEntryInline(admin.TabularInline):
    model = ScheduleEntry
    extra = 1


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'operator', 'origin', 'destination', 'color', 'duration_minutes', 'is_active')
    list_filter = ('is_active', 'operator')
    search_fields = ('name', 'code', 'origin', 'destination')
    inlines = [RouteStopInline, ScheduleEntryInline]
    list_editable = ('is_active',)
    autocomplete_fields = ['operator']


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'address', 'latitude', 'longitude', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'address')


@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = ('route', 'day_type', 'departure_time', 'frequency_minutes')
    list_filter = ('day_type', 'route')
