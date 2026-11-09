from django.conf import settings
from django.db import models


class Order(models.Model):
	class Status(models.TextChoices):
		IN_PROGRESS = "in_progress", "In progress"
		COMPLETED = "completed", "Completed"
		CANCELLED = "cancelled", "Cancelled"

	customer_user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="orders_as_customer",
	)
	business_user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="orders_as_business",
	)
	title = models.CharField(max_length=255)
	revisions = models.PositiveIntegerField()
	delivery_time_in_days = models.PositiveIntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	features = models.JSONField(default=list)
	offer_type = models.CharField(max_length=8)
	status = models.CharField(max_length=11, choices=Status.choices, default=Status.IN_PROGRESS)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.title} ({self.status})"
