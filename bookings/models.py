"""
Models for the bookings application.

Entities:
  - Resource: A bookable resource (room, equipment, etc.)
  - Booking:  A reservation of a Resource by a User
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class ResourceCategory(models.Model):
    """Category / type of resource (e.g. Meeting Room, Lab, Equipment)."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Emoji or icon identifier shown in the UI",
    )

    class Meta:
        verbose_name = "Resource Category"
        verbose_name_plural = "Resource Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Resource(models.Model):
    """A bookable resource."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(default=1)
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources",
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self):
        return self.name

    def is_available(self, start_time, end_time, exclude_booking_id=None):
        """Return True if the resource has no confirmed bookings in the given window."""
        qs = self.bookings.filter(
            status=Booking.Status.CONFIRMED,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )
        if exclude_booking_id:
            qs = qs.exclude(pk=exclude_booking_id)
        return not qs.exists()


class Booking(models.Model):
    """A reservation of a Resource by a User."""

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        PENDING = "pending", "Pending"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        db_index=True,
    )
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="bookings",
        db_index=True,
    )
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["resource", "start_time", "end_time"]),
            models.Index(fields=["start_time", "end_time"]),
        ]

    def __str__(self):
        return f"{self.title} – {self.resource.name} ({self.start_time:%Y-%m-%d %H:%M})"

    @property
    def is_upcoming(self):
        return self.start_time > timezone.now() and self.status == self.Status.CONFIRMED

    @property
    def duration_hours(self):
        delta = self.end_time - self.start_time
        return round(delta.total_seconds() / 3600, 2)
