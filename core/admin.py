from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Team, Membership, Experiment, Measurement


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "name", "username", "is_staff")
    search_fields = ("email", "name", "username")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name", "username")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "username", "password1", "password2"),
            },
        ),
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "role")
    list_filter = ("role",)
    search_fields = ("user__name", "user__email", "team__name")


admin.site.register(Experiment)
admin.site.register(Measurement)
