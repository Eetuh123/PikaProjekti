"""
Comprehensive unit tests for the bookings application.

Run with:
    python manage.py test bookings
    coverage run manage.py test bookings && coverage report
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import Booking, Resource, ResourceCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(username="testuser", password="TestPass123!"):
    return User.objects.create_user(username=username, password=password, email=f"{username}@example.com")


def make_category(name="Meeting Room", icon="🏢"):
    return ResourceCategory.objects.create(name=name, icon=icon)


def make_resource(name="Room A", category=None, capacity=10, is_active=True):
    return Resource.objects.create(
        name=name,
        category=category,
        capacity=capacity,
        location="Floor 1",
        is_active=is_active,
    )


def future(hours=2):
    return timezone.now() + timedelta(hours=hours)


def make_booking(user, resource, title="Test Booking", offset_hours=2, duration_hours=1, status=Booking.Status.CONFIRMED):
    start = timezone.now() + timedelta(hours=offset_hours)
    end = start + timedelta(hours=duration_hours)
    return Booking.objects.create(
        user=user,
        resource=resource,
        title=title,
        start_time=start,
        end_time=end,
        status=status,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class ResourceCategoryModelTest(TestCase):
    def test_str(self):
        cat = make_category("Lab")
        self.assertEqual(str(cat), "Lab")

    def test_ordering(self):
        make_category("Zebra")
        make_category("Alpha")
        names = list(ResourceCategory.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class ResourceModelTest(TestCase):
    def setUp(self):
        self.cat = make_category()
        self.resource = make_resource(category=self.cat)

    def test_str(self):
        self.assertEqual(str(self.resource), "Room A")

    def test_is_available_no_bookings(self):
        self.assertTrue(self.resource.is_available(future(1), future(3)))

    def test_is_available_with_conflict(self):
        user = make_user()
        make_booking(user, self.resource, offset_hours=2, duration_hours=2)
        # Overlapping window
        self.assertFalse(self.resource.is_available(future(1), future(4)))

    def test_is_available_adjacent_bookings(self):
        user = make_user()
        make_booking(user, self.resource, offset_hours=2, duration_hours=1)
        # Starts exactly when previous ends — should be available
        self.assertTrue(self.resource.is_available(future(3), future(5)))

    def test_is_available_exclude_self(self):
        user = make_user()
        booking = make_booking(user, self.resource, offset_hours=2, duration_hours=2)
        # Same window but excluding the booking itself
        self.assertTrue(
            self.resource.is_available(future(2), future(4), exclude_booking_id=booking.pk)
        )

    def test_inactive_resource_not_in_default_queryset(self):
        inactive = make_resource(name="Inactive", is_active=False)
        active_names = list(Resource.objects.filter(is_active=True).values_list("name", flat=True))
        self.assertNotIn("Inactive", active_names)


class BookingModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.resource = make_resource()
        self.booking = make_booking(self.user, self.resource)

    def test_str(self):
        self.assertIn("Test Booking", str(self.booking))
        self.assertIn("Room A", str(self.booking))

    def test_is_upcoming_true(self):
        self.assertTrue(self.booking.is_upcoming)

    def test_is_upcoming_false_past(self):
        past_booking = Booking.objects.create(
            user=self.user,
            resource=self.resource,
            title="Past",
            start_time=timezone.now() - timedelta(hours=3),
            end_time=timezone.now() - timedelta(hours=1),
            status=Booking.Status.CONFIRMED,
        )
        self.assertFalse(past_booking.is_upcoming)

    def test_is_upcoming_false_cancelled(self):
        self.booking.status = Booking.Status.CANCELLED
        self.booking.save()
        self.assertFalse(self.booking.is_upcoming)

    def test_duration_hours(self):
        self.assertEqual(self.booking.duration_hours, 1.0)

    def test_status_choices(self):
        choices = [c[0] for c in Booking.Status.choices]
        self.assertIn("confirmed", choices)
        self.assertIn("cancelled", choices)
        self.assertIn("pending", choices)


# ---------------------------------------------------------------------------
# View tests — authentication
# ---------------------------------------------------------------------------


class AuthViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_get(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create an account")

    def test_register_post_valid(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "StrongPass99!",
                "password2": "StrongPass99!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_post_invalid(self):
        response = self.client.post(
            reverse("register"),
            {"username": "", "email": "bad", "password1": "a", "password2": "b"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="bad").exists())

    def test_login_get(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_post_valid(self):
        make_user("loginuser", "TestPass123!")
        response = self.client.post(
            reverse("login"), {"username": "loginuser", "password": "TestPass123!"}
        )
        self.assertEqual(response.status_code, 302)

    def test_login_post_invalid(self):
        response = self.client.post(
            reverse("login"), {"username": "nobody", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)

    def test_logout_requires_post(self):
        user = make_user()
        self.client.force_login(user)
        response = self.client.get(reverse("logout"))
        # GET should not log out (405 or redirect)
        self.assertNotEqual(response.status_code, 200)

    def test_logout_post(self):
        user = make_user()
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)

    def test_register_redirects_if_authenticated(self):
        user = make_user()
        self.client.force_login(user)
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# View tests — resources
# ---------------------------------------------------------------------------


class ResourceViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = make_category()
        self.resource = make_resource(category=self.cat)

    def test_resource_list_public(self):
        response = self.client.get(reverse("resource_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Room A")

    def test_resource_list_filter_by_category(self):
        other_cat = make_category("Lab")
        make_resource("Lab Room", category=other_cat)
        response = self.client.get(reverse("resource_list") + f"?category={self.cat.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Room A")
        self.assertNotContains(response, "Lab Room")

    def test_resource_detail_public(self):
        response = self.client.get(reverse("resource_detail", args=[self.resource.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Room A")

    def test_resource_detail_404_inactive(self):
        inactive = make_resource("Inactive", is_active=False)
        response = self.client.get(reverse("resource_detail", args=[inactive.pk]))
        self.assertEqual(response.status_code, 404)

    def test_resource_detail_404_nonexistent(self):
        response = self.client.get(reverse("resource_detail", args=[99999]))
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# View tests — bookings
# ---------------------------------------------------------------------------


class BookingViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.other_user = make_user("other", "OtherPass123!")
        self.resource = make_resource()
        self.client.force_login(self.user)

    def test_booking_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("booking_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_booking_list_shows_own_bookings(self):
        booking = make_booking(self.user, self.resource)
        other_booking = make_booking(self.other_user, self.resource, title="Other Booking", offset_hours=10)
        response = self.client.get(reverse("booking_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, booking.title)
        self.assertNotContains(response, other_booking.title)

    def test_booking_list_status_filter(self):
        make_booking(self.user, self.resource, title="ConfirmedBooking", offset_hours=2)
        make_booking(self.user, self.resource, title="CancelledBooking", offset_hours=10, status=Booking.Status.CANCELLED)
        response = self.client.get(reverse("booking_list") + "?status=confirmed")
        self.assertContains(response, "ConfirmedBooking")
        self.assertNotContains(response, "CancelledBooking")

    def test_booking_create_get(self):
        response = self.client.get(reverse("booking_create"))
        self.assertEqual(response.status_code, 200)

    def test_booking_create_post_valid(self):
        start = timezone.now() + timedelta(hours=5)
        end = start + timedelta(hours=2)
        response = self.client.post(
            reverse("booking_create"),
            {
                "resource": self.resource.pk,
                "title": "New Meeting",
                "start_time": start.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end.strftime("%Y-%m-%dT%H:%M"),
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Booking.objects.filter(title="New Meeting", user=self.user).exists())

    def test_booking_create_post_conflict(self):
        make_booking(self.user, self.resource, offset_hours=5, duration_hours=2)
        start = timezone.now() + timedelta(hours=5)
        end = start + timedelta(hours=2)
        response = self.client.post(
            reverse("booking_create"),
            {
                "resource": self.resource.pk,
                "title": "Conflicting",
                "start_time": start.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end.strftime("%Y-%m-%dT%H:%M"),
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)  # form re-rendered with error
        self.assertFalse(Booking.objects.filter(title="Conflicting").exists())

    def test_booking_create_past_start(self):
        start = timezone.now() - timedelta(hours=1)
        end = start + timedelta(hours=2)
        response = self.client.post(
            reverse("booking_create"),
            {
                "resource": self.resource.pk,
                "title": "Past Booking",
                "start_time": start.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end.strftime("%Y-%m-%dT%H:%M"),
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_booking_detail_own(self):
        booking = make_booking(self.user, self.resource)
        response = self.client.get(reverse("booking_detail", args=[booking.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, booking.title)

    def test_booking_detail_other_user_404(self):
        booking = make_booking(self.other_user, self.resource, offset_hours=20)
        response = self.client.get(reverse("booking_detail", args=[booking.pk]))
        self.assertEqual(response.status_code, 404)

    def test_booking_cancel_get_shows_confirm(self):
        booking = make_booking(self.user, self.resource)
        response = self.client.get(reverse("booking_cancel", args=[booking.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cancel this booking")

    def test_booking_cancel_post(self):
        booking = make_booking(self.user, self.resource)
        response = self.client.post(reverse("booking_cancel", args=[booking.pk]))
        self.assertEqual(response.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    def test_booking_cancel_other_user_404(self):
        booking = make_booking(self.other_user, self.resource, offset_hours=20)
        response = self.client.post(reverse("booking_cancel", args=[booking.pk]))
        self.assertEqual(response.status_code, 404)

    def test_booking_cancel_already_cancelled(self):
        booking = make_booking(self.user, self.resource, status=Booking.Status.CANCELLED)
        response = self.client.post(reverse("booking_cancel", args=[booking.pk]))
        self.assertEqual(response.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    def test_booking_create_with_resource_preselected(self):
        response = self.client.get(
            reverse("booking_create") + f"?resource={self.resource.pk}"
        )
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Home view test
# ---------------------------------------------------------------------------


class HomeViewTest(TestCase):
    def test_home_public(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BookIt")


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


class APIResourceTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.cat = make_category()
        self.resource = make_resource(category=self.cat)

    def test_resource_list_unauthenticated(self):
        response = self.client.get("/api/resources/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_resource_list_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/resources/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_resource_detail(self):
        response = self.client.get(f"/api/resources/{self.resource.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Room A")

    def test_resource_list_filter_by_category(self):
        self.client.force_authenticate(user=self.user)
        other_cat = make_category("Lab")
        make_resource("Lab Room", category=other_cat)
        response = self.client.get(f"/api/resources/?category={self.cat.pk}")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Room A")

    def test_category_list(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class APIBookingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.other_user = make_user("other2", "OtherPass123!")
        self.resource = make_resource()
        self.client.force_authenticate(user=self.user)

    def test_booking_list_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/bookings/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_booking_list_own_only(self):
        make_booking(self.user, self.resource, title="Mine")
        make_booking(self.other_user, self.resource, title="Theirs", offset_hours=10)
        response = self.client.get("/api/bookings/")
        titles = [b["title"] for b in response.data["results"]]
        self.assertIn("Mine", titles)
        self.assertNotIn("Theirs", titles)

    def test_booking_create_valid(self):
        start = timezone.now() + timedelta(hours=5)
        end = start + timedelta(hours=2)
        response = self.client.post(
            "/api/bookings/",
            {
                "resource_id": self.resource.pk,
                "title": "API Booking",
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "API Booking")
        self.assertEqual(response.data["user"]["username"], "testuser")

    def test_booking_create_conflict(self):
        make_booking(self.user, self.resource, offset_hours=5, duration_hours=2)
        start = timezone.now() + timedelta(hours=5)
        end = start + timedelta(hours=2)
        response = self.client.post(
            "/api/bookings/",
            {
                "resource_id": self.resource.pk,
                "title": "Conflict",
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_create_end_before_start(self):
        start = timezone.now() + timedelta(hours=5)
        end = start - timedelta(hours=1)
        response = self.client.post(
            "/api/bookings/",
            {
                "resource_id": self.resource.pk,
                "title": "Bad Times",
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_detail_own(self):
        booking = make_booking(self.user, self.resource)
        response = self.client.get(f"/api/bookings/{booking.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_booking_detail_other_user_404(self):
        booking = make_booking(self.other_user, self.resource, offset_hours=20)
        response = self.client.get(f"/api/bookings/{booking.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_booking_cancel_api(self):
        booking = make_booking(self.user, self.resource)
        response = self.client.post(f"/api/bookings/{booking.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")

    def test_booking_cancel_api_already_cancelled(self):
        booking = make_booking(self.user, self.resource, status=Booking.Status.CANCELLED)
        response = self.client.post(f"/api/bookings/{booking.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_cancel_api_other_user_404(self):
        booking = make_booking(self.other_user, self.resource, offset_hours=20)
        response = self.client.post(f"/api/bookings/{booking.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_root(self):
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("bookings", response.data)

    def test_booking_list_status_filter(self):
        make_booking(self.user, self.resource, title="Confirmed", offset_hours=2)
        make_booking(self.user, self.resource, title="Cancelled", offset_hours=10, status=Booking.Status.CANCELLED)
        response = self.client.get("/api/bookings/?status=confirmed")
        titles = [b["title"] for b in response.data["results"]]
        self.assertIn("Confirmed", titles)
        self.assertNotIn("Cancelled", titles)


# ---------------------------------------------------------------------------
# Form tests
# ---------------------------------------------------------------------------


class BookingFormTest(TestCase):
    def setUp(self):
        self.resource = make_resource()

    def test_valid_form(self):
        from .forms import BookingForm

        start = timezone.now() + timedelta(hours=5)
        end = start + timedelta(hours=2)
        form = BookingForm(
            data={
                "resource": self.resource.pk,
                "title": "Form Test",
                "start_time": start.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end.strftime("%Y-%m-%dT%H:%M"),
                "notes": "",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_end_before_start(self):
        from .forms import BookingForm

        start = timezone.now() + timedelta(hours=5)
        end = start - timedelta(hours=1)
        form = BookingForm(
            data={
                "resource": self.resource.pk,
                "title": "Bad",
                "start_time": start.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end.strftime("%Y-%m-%dT%H:%M"),
                "notes": "",
            }
        )
        self.assertFalse(form.is_valid())

    def test_inactive_resource_not_in_choices(self):
        from .forms import BookingForm

        inactive = make_resource("Inactive", is_active=False)
        form = BookingForm()
        resource_pks = [r.pk for r in form.fields["resource"].queryset]
        self.assertNotIn(inactive.pk, resource_pks)


class RegisterFormTest(TestCase):
    def test_valid_registration(self):
        from .forms import RegisterForm

        form = RegisterForm(
            data={
                "username": "formuser",
                "email": "form@example.com",
                "first_name": "Form",
                "last_name": "User",
                "password1": "StrongPass99!",
                "password2": "StrongPass99!",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        from .forms import RegisterForm

        form = RegisterForm(
            data={
                "username": "formuser2",
                "email": "form2@example.com",
                "password1": "StrongPass99!",
                "password2": "DifferentPass99!",
            }
        )
        self.assertFalse(form.is_valid())
