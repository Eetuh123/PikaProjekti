"""
Django admin configuration for the bookings application.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Booking, Resource, ResourceCategory


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "resource_count")
    search_fields = ("name",)

    def resource_count(self, obj):
        return obj.resources.count()

    resource_count.short_description = "Resources"


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "location", "capacity", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "location", "description")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "category", "description")}),
        ("Details", {"fields": ("location", "capacity", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "resource",
        "start_time",
        "end_time",
        "status_badge",
        "created_at",
    )
    list_filter = ("status", "resource", "start_time")
    search_fields = ("title", "user__username", "user__email", "resource__name")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "start_time"
    raw_id_fields = ("user", "resource")
    fieldsets = (
        (None, {"fields": ("user", "resource", "title", "notes")}),
        ("Schedule", {"fields": ("start_time", "end_time", "status")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def status_badge(self, obj):
        colours = {
            "confirmed": "#16a34a",
            "cancelled": "#dc2626",
            "pending": "#d97706",
        }
        colour = colours.get(obj.status, "#6b7280")
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            colour,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"
