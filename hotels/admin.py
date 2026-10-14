from django.contrib import admin
from .models import Hotel, HotelImage


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'approx_price', 'address', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address', 'services')
    inlines = [HotelImageInline]
    list_editable = ('is_active',)
