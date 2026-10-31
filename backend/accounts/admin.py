from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class AuditKMUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("AuditKM", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("AuditKM", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = UserAdmin.list_filter + ("role",)
