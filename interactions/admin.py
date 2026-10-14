from django.contrib import admin
from .models import Favorite, Comment, Rating, HistoryEntry, ContentFlag


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'object_id', 'created_at')
    list_filter = ('content_type',)
    search_fields = ('user__username', 'user__email')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'object_id', 'body_preview', 'created_at', 'is_edited')
    list_filter = ('content_type', 'is_edited')
    search_fields = ('user__username', 'body')

    def body_preview(self, obj):
        return obj.body[:60]
    body_preview.short_description = 'Comentario'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'object_id', 'score', 'created_at')
    list_filter = ('content_type', 'score')


@admin.register(HistoryEntry)
class HistoryEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'content_type', 'object_id', 'created_at')
    list_filter = ('kind',)
    date_hierarchy = 'created_at'


@admin.register(ContentFlag)
class ContentFlagAdmin(admin.ModelAdmin):
    list_display = ('comment', 'reported_by', 'reason', 'resolved', 'created_at')
    list_filter = ('reason', 'resolved')
    list_editable = ('resolved',)
