from django.db import models
from django.contrib.auth.models import User


class RoleProfile(models.Model):
	ROLE_CHOICES = [
		("customer", "Customer"),
		("staff", "Staff"),
		("manager", "Manager"),
		("admin", "Admin"),
	]

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="role_profile")
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.user.username} ({self.role})"
