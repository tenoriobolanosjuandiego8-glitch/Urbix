from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'content_preview', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'content')
    date_hierarchy = 'created_at'

    def content_preview(self, obj):
        return obj.content[:60]
    content_preview.short_description = 'Mensaje'
