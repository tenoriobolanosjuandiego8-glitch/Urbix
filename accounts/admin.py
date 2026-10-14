from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DriverProfile, ActivityLog, EmergencyContact, LoginAttempt


@admin.register(User)
class URBIXUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'email_verified', 'created_at')
    list_filter = ('role', 'is_active', 'email_verified', 'city')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    fieldsets = UserAdmin.fieldsets + (
        ('URBIX', {'fields': ('role', 'phone', 'city', 'avatar', 'email_verified', 'remember_session')}),
    )


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'status', 'assigned_bus', 'assigned_route', 'hired_at')
    list_filter = ('status',)
    search_fields = ('user__first_name', 'user__last_name', 'license_number')
    autocomplete_fields = ('user', 'assigned_bus', 'assigned_route')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'path', 'ip_address', 'created_at')
    list_filter = ('method',)
    search_fields = ('user__username', 'path', 'ip_address')
    readonly_fields = [f.name for f in ActivityLog._meta.fields]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'phone', 'relationship', 'created_at')
    search_fields = ('user__username', 'name', 'phone')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'ip_address', 'success', 'created_at')
    list_filter = ('success',)
    search_fields = ('email', 'ip_address')
    readonly_fields = [f.name for f in LoginAttempt._meta.fields]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False
