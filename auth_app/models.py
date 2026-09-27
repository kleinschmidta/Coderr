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
