from django.contrib import admin
from .models import Restaurant, RestaurantImage


class RestaurantImageInline(admin.TabularInline):
    model = RestaurantImage
    extra = 1


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'price_range', 'address', 'is_active')
    list_filter = ('tag', 'price_range', 'is_active')
    search_fields = ('name', 'address', 'description')
    inlines = [RestaurantImageInline]
    list_editable = ('is_active',)
