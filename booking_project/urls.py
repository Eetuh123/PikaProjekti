"""
Root URL configuration for booking_project.
"""

from django.contrib import admin
from django.urls import include, path

from bookings.views import home, login_view, logout_view, register_view

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Home
    path("", home, name="home"),
    # Auth
    path("accounts/register/", register_view, name="register"),
    path("accounts/login/", login_view, name="login"),
    path("accounts/logout/", logout_view, name="logout"),
    # App
    path("", include("bookings.urls")),
    # REST API
    path("api/", include("bookings.api_urls")),
]
