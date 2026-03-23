"""
Views for the bookings application.

Covers:
  - Authentication (register, login, logout)
  - Resource listing
  - Booking CRUD (list, create, detail, cancel)
  - Home / landing page
"""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BookingForm, RegisterForm, LoginForm
from .models import Booking, Resource, ResourceCategory


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------


def home(request):
    """Public landing page."""
    categories = ResourceCategory.objects.all()
    active_resources = Resource.objects.filter(is_active=True).select_related("category")[:6]
    context = {
        "categories": categories,
        "active_resources": active_resources,
    }
    return render(request, "home.html", context)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def register_view(request):
    """User registration."""
    if request.user.is_authenticated:
        return redirect("booking_list")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect("booking_list")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("booking_list")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get("next", "booking_list")
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})

@require_POST
def logout_view(request):
    """User logout (POST only for CSRF safety)."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


def resource_list(request):
    """Public list of all active resources."""
    category_id = request.GET.get("category")
    resources = Resource.objects.filter(is_active=True).select_related("category")
    categories = ResourceCategory.objects.all()

    if category_id:
        resources = resources.filter(category_id=category_id)

    context = {
        "resources": resources,
        "categories": categories,
        "selected_category": category_id,
    }
    return render(request, "bookings/resource_list.html", context)


def resource_detail(request, pk):
    """Detail page for a single resource with availability info."""
    resource = get_object_or_404(Resource, pk=pk, is_active=True)
    upcoming_bookings = resource.bookings.filter(
        status=Booking.Status.CONFIRMED,
        end_time__gte=timezone.now(),
    ).order_by("start_time")[:10]

    context = {
        "resource": resource,
        "upcoming_bookings": upcoming_bookings,
    }
    return render(request, "bookings/resource_detail.html", context)


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------


@login_required
def booking_list(request):
    """List the current user's bookings."""
    status_filter = request.GET.get("status", "")
    bookings = Booking.objects.filter(user=request.user).select_related("resource", "resource__category")

    if status_filter in [s.value for s in Booking.Status]:
        bookings = bookings.filter(status=status_filter)

    context = {
        "bookings": bookings,
        "status_filter": status_filter,
        "status_choices": Booking.Status.choices,
    }
    return render(request, "bookings/booking_list.html", context)


@login_required
def booking_create(request):
    """Create a new booking."""
    resource_id = request.GET.get("resource")
    initial = {}
    if resource_id:
        try:
            initial["resource"] = Resource.objects.get(pk=resource_id, is_active=True)
        except Resource.DoesNotExist:
            pass

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            messages.success(request, f'Booking "{booking.title}" confirmed!')
            return redirect("booking_detail", pk=booking.pk)
    else:
        form = BookingForm(initial=initial)

    return render(request, "bookings/booking_form.html", {"form": form, "action": "Create"})


@login_required
def booking_detail(request, pk):
    """Detail view for a single booking."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, "bookings/booking_detail.html", {"booking": booking})


@login_required
def booking_cancel(request, pk):
    """Cancel a booking (POST only)."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if request.method == "POST":
        if booking.status == Booking.Status.CONFIRMED:
            booking.status = Booking.Status.CANCELLED
            booking.save(update_fields=["status", "updated_at"])
            messages.success(request, f'Booking "{booking.title}" has been cancelled.')
        else:
            messages.warning(request, "This booking cannot be cancelled.")
        return redirect("booking_list")

    return render(request, "bookings/booking_cancel_confirm.html", {"booking": booking})