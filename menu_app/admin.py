from django.contrib import admin

from .models import MenuItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("title", "parent", "url_name", "order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("title", "url_name", "permission")
    filter_horizontal = ("users", "groups")
    ordering = ("order", "id")
