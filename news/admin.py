from django.contrib import admin

from .models import FocusNews


@admin.register(FocusNews)
class FocusNewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'published_at', 'created_at')
    search_fields = ('title', 'author')
    readonly_fields = ('created_at',)
