from django.contrib import admin
from .models import Business, BusinessImage, BusinessPromotion, BusinessEvent, Subscription


class BusinessImageInline(admin.TabularInline):
    model = BusinessImage
    extra = 1


class PromotionInline(admin.TabularInline):
    model = BusinessPromotion
    extra = 0


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_type', 'owner', 'status', 'plan', 'views_count', 'clicks_count', 'created_at')
    list_filter = ('status', 'plan', 'business_type')
    search_fields = ('name', 'owner__username', 'owner__email', 'address')
    inlines = [BusinessImageInline, PromotionInline]
    readonly_fields = ('views_count', 'clicks_count', 'verified_at', 'verified_by')
    autocomplete_fields = ['owner']


@admin.register(BusinessPromotion)
class BusinessPromotionAdmin(admin.ModelAdmin):
    list_display = ('business', 'title', 'discount_text', 'valid_until', 'is_active')
    list_filter = ('is_active',)


@admin.register(BusinessEvent)
class BusinessEventAdmin(admin.ModelAdmin):
    list_display = ('business', 'kind', 'created_at')
    list_filter = ('kind',)
    date_hierarchy = 'created_at'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('business', 'plan', 'provider', 'amount_cop', 'status', 'created_at', 'paid_at')
    list_filter = ('provider', 'status', 'plan')
