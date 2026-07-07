from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import UserProfile
from .forms import CustomUserCreationForm


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "account_type",
                "password1",
                "password2",
                "groups",
                "is_staff",
                "is_active",
            ),
        }),
    )

    list_display = (
        "username",
        "get_account_type",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return [UserProfileInline(self.model, self.admin_site)]

    def get_account_type(self, obj):
        if hasattr(obj, "profile"):
            return obj.profile.get_account_type_display()
        return "Not Set"

    get_account_type.short_description = "Account Type"

    class Media:
        js = ("accounts/js/user_admin.js",)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)