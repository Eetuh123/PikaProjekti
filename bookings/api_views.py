"""
Django REST Framework API views for the bookings application.
"""

from rest_framework import filters, generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Booking, Resource, ResourceCategory
from .serializers import BookingSerializer, ResourceCategorySerializer, ResourceSerializer


# ---------------------------------------------------------------------------
# Resource endpoints (read-only for all authenticated users)
# ---------------------------------------------------------------------------


class ResourceCategoryListView(generics.ListAPIView):
    """GET /api/categories/ — list all resource categories."""

    queryset = ResourceCategory.objects.all()
    serializer_class = ResourceCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ResourceListView(generics.ListAPIView):
    """GET /api/resources/ — list active resources, filterable by category."""

    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "location", "description"]
    ordering_fields = ["name", "capacity", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        qs = Resource.objects.filter(is_active=True).select_related("category")
        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs


class ResourceDetailView(generics.RetrieveAPIView):
    """GET /api/resources/<pk>/ — retrieve a single resource."""

    queryset = Resource.objects.filter(is_active=True).select_related("category")
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# ---------------------------------------------------------------------------
# Booking endpoints (authenticated users, own bookings only)
# ---------------------------------------------------------------------------


class BookingListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/bookings/ — list current user's bookings.
    POST /api/bookings/ — create a new booking.
    """

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["start_time", "created_at", "status"]
    ordering = ["-start_time"]

    def get_queryset(self):
        qs = Booking.objects.filter(user=self.request.user).select_related(
            "resource", "resource__category"
        )
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class BookingDetailView(generics.RetrieveAPIView):
    """GET /api/bookings/<pk>/ — retrieve a single booking (owner only)."""

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related(
            "resource", "resource__category"
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def booking_cancel_api(request, pk):
    """POST /api/bookings/<pk>/cancel/ — cancel a booking."""
    try:
        booking = Booking.objects.get(pk=pk, user=request.user)
    except Booking.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if booking.status != Booking.Status.CONFIRMED:
        return Response(
            {"detail": "Only confirmed bookings can be cancelled."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status", "updated_at"])
    serializer = BookingSerializer(booking, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def api_root(request):
    """GET /api/ — API overview."""
    return Response(
        {
            "categories": request.build_absolute_uri("/api/categories/"),
            "resources": request.build_absolute_uri("/api/resources/"),
            "bookings": request.build_absolute_uri("/api/bookings/"),
        }
    )
