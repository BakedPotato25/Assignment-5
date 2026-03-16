from django.contrib import admin

from .models import RoleProfile


@admin.register(RoleProfile)
class RoleProfileAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "role", "created_at")
	search_fields = ("user__username", "user__email", "role")
