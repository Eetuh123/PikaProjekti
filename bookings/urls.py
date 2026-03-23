"""
URL configuration for the bookings application.
"""

from django.urls import path

from . import views

urlpatterns = [
    # Resources
    path("resources/", views.resource_list, name="resource_list"),
    path("resources/<int:pk>/", views.resource_detail, name="resource_detail"),
    # Bookings
    path("bookings/", views.booking_list, name="booking_list"),
    path("bookings/new/", views.booking_create, name="booking_create"),
    path("bookings/<int:pk>/", views.booking_detail, name="booking_detail"),
    path("bookings/<int:pk>/cancel/", views.booking_cancel, name="booking_cancel"),
]
