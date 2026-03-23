"""
API URL configuration for the bookings application.
"""

from django.urls import path

from .api_views import (
    BookingDetailView,
    BookingListCreateView,
    ResourceCategoryListView,
    ResourceDetailView,
    ResourceListView,
    api_root,
    booking_cancel_api,
)

urlpatterns = [
    path("", api_root, name="api_root"),
    path("categories/", ResourceCategoryListView.as_view(), name="api_category_list"),
    path("resources/", ResourceListView.as_view(), name="api_resource_list"),
    path("resources/<int:pk>/", ResourceDetailView.as_view(), name="api_resource_detail"),
    path("bookings/", BookingListCreateView.as_view(), name="api_booking_list"),
    path("bookings/<int:pk>/", BookingDetailView.as_view(), name="api_booking_detail"),
    path("bookings/<int:pk>/cancel/", booking_cancel_api, name="api_booking_cancel"),
]
