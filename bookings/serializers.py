"""
DRF serializers for the bookings application.
"""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Booking, Resource, ResourceCategory


class ResourceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceCategory
        fields = ["id", "name", "description", "icon"]


class ResourceSerializer(serializers.ModelSerializer):
    category = ResourceCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ResourceCategory.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Resource
        fields = [
            "id",
            "name",
            "description",
            "location",
            "capacity",
            "category",
            "category_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class BookingUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class BookingSerializer(serializers.ModelSerializer):
    user = BookingUserSerializer(read_only=True)
    resource = ResourceSerializer(read_only=True)
    resource_id = serializers.PrimaryKeyRelatedField(
        queryset=Resource.objects.filter(is_active=True),
        source="resource",
        write_only=True,
    )
    duration_hours = serializers.FloatField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "resource",
            "resource_id",
            "title",
            "notes",
            "start_time",
            "end_time",
            "status",
            "duration_hours",
            "is_upcoming",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        resource = attrs.get("resource")

        from django.utils import timezone

        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError("End time must be after start time.")
            if start_time < timezone.now():
                raise serializers.ValidationError("Start time cannot be in the past.")
            if resource:
                exclude_id = self.instance.pk if self.instance else None
                if not resource.is_available(start_time, end_time, exclude_booking_id=exclude_id):
                    raise serializers.ValidationError(
                        f'"{resource.name}" is already booked for the selected time slot.'
                    )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
