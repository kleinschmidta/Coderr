from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
	class UserType(models.TextChoices):
		CUSTOMER = "customer", "Customer"
		BUSINESS = "business", "Business"

	type = models.CharField(
		max_length=8,
		choices=UserType.choices,
	)
	location = models.CharField(max_length=255, blank=True)
	tel = models.CharField(max_length=30, blank=True)
	description = models.TextField(blank=True)
	working_hours = models.CharField(max_length=255, blank=True)
	file = models.CharField(max_length=255, blank=True)
	uploaded_at = models.DateTimeField(null=True, blank=True)
