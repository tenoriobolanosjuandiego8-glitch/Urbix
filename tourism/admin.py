from django.contrib import admin
from .models import TouristPlace, TouristPlaceImage


class TouristPlaceImageInline(admin.TabularInline):
    model = TouristPlaceImage
    extra = 1


@admin.register(TouristPlace)
class TouristPlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'is_active')
    list_filter = ('tag', 'is_active')
    search_fields = ('name', 'history', 'curiosities')
    inlines = [TouristPlaceImageInline]
    list_editable = ('is_active',)
