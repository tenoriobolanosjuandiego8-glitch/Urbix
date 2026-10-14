from django.contrib import admin
from .models import Report, DriverShift


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('driver', 'kind', 'bus', 'route', 'status', 'created_at')
    list_filter = ('kind', 'status')
    search_fields = ('driver__username', 'description')
    date_hierarchy = 'created_at'
    list_editable = ('status',)


@admin.register(DriverShift)
class DriverShiftAdmin(admin.ModelAdmin):
    list_display = ('driver', 'route', 'bus', 'lap_number', 'started_at', 'ended_at', 'on_time')
    list_filter = ('on_time', 'route')
    search_fields = ('driver__username',)
