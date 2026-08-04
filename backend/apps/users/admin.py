from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "full_name", "role", "is_verified", "is_active", "created_at")
    list_filter = ("role", "is_verified", "is_active", "is_staff")
    search_fields = ("email", "full_name")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "last_login", "deleted_at")

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal", {"fields": ("full_name", "preferred_language")}),
        ("Status", {"fields": ("role", "is_verified", "is_active", "is_staff", "is_superuser")}),
        ("Usage", {"fields": ("daily_upload_count", "last_upload_reset")}),
        ("Timestamps", {"fields": ("created_at", "last_login", "deleted_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "full_name", "role"),
        }),
    )
