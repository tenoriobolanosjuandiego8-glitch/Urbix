from django.contrib import admin
from .models import Event, EventImage


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'place', 'start_at', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'place', 'description')
    date_hierarchy = 'start_at'
    inlines = [EventImageInline]
    list_editable = ('is_active',)
