# AGENTS.md — Project Structure & Architecture Guide

This document describes the structure, conventions, and key design decisions of the **BookIt** Django booking system. It is intended for AI agents, new contributors, and automated tooling.

---

## Project Overview

**BookIt** is a Django 4.2 web application that allows users to browse bookable resources (rooms, equipment, facilities) and make time-slot reservations. It exposes both a server-rendered HTML interface and a Django REST Framework JSON API.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | Django 4.2 |
| REST API | Django REST Framework 3.x |
| Database | PostgreSQL (psycopg2-binary) / SQLite (dev) |
| Environment config | django-environ |
| Frontend styling | Tailwind CSS (CDN Play build) |
| Theme system | CSS custom properties (`var()`) |
| Testing | Django TestCase + DRF APIClient + coverage |
| Python | 3.11+ |

---

## Directory Structure

```
PikaProjekti/
│
├── booking_project/            # Django project package
│   ├── __init__.py
│   ├── settings.py             # All settings; reads from .env via django-environ
│   ├── urls.py                 # Root URL dispatcher
│   ├── asgi.py
│   └── wsgi.py
│
├── bookings/                   # Single Django application
│   ├── __init__.py
│   ├── models.py               # Data models (see Models section)
│   ├── views.py                # HTML views (function-based)
│   ├── api_views.py            # DRF class-based + function-based API views
│   ├── serializers.py          # DRF serializers
│   ├── forms.py                # Django ModelForms
│   ├── admin.py                # Django admin registrations
│   ├── urls.py                 # HTML URL patterns (included at root)
│   ├── api_urls.py             # API URL patterns (included at /api/)
│   ├── tests.py                # All unit tests
│   ├── apps.py
│   ├── migrations/             # Database migrations
│   └── fixtures/
│       └── initial_data.json   # Seed data (categories + resources)
│
├── templates/                  # Django templates (global, not per-app)
│   ├── base.html               # Master layout with nav, messages, footer
│   ├── home.html               # Public landing page
│   ├── accounts/
│   │   ├── login.html
│   │   └── register.html
│   └── bookings/
│       ├── resource_list.html
│       ├── resource_detail.html
│       ├── booking_list.html
│       ├── booking_form.html
│       ├── booking_detail.html
│       └── booking_cancel_confirm.html
│
├── static/
│   ├── css/
│   │   └── theme.css           # CSS custom properties for light/dark mode
│   └── js/
│       └── theme.js            # Theme toggle (reads/writes localStorage)
│
├── venv/                       # Virtual environment (not committed)
├── .env                        # Secrets (not committed)
├── .env.example                # Template for .env
├── manage.py
├── README.md
├── TODO.md
└── AGENTS.md                   # This file
```

---

## Models

All models live in `bookings/models.py`.

### `ResourceCategory`
- Represents a type of resource (e.g. "Meeting Room", "Lab")
- Fields: `name` (unique), `description`, `icon` (emoji string)
- Ordered alphabetically by `name`

### `Resource`
- A bookable item
- Fields: `name`, `description`, `location`, `capacity`, `category` (FK → ResourceCategory), `is_active`, timestamps
- Key method: `is_available(start_time, end_time, exclude_booking_id=None)` — checks for confirmed booking conflicts using ORM (no raw SQL)
- Indexes: `(is_active, name)`, FK on `category`

### `Booking`
- A reservation of a `Resource` by a `User`
- Fields: `user` (FK → AUTH_USER_MODEL), `resource` (FK → Resource), `title`, `notes`, `start_time`, `end_time`, `status` (TextChoices: confirmed/cancelled/pending), timestamps
- Properties: `is_upcoming`, `duration_hours`
- Indexes: `(user, status)`, `(resource, start_time, end_time)`, `(start_time, end_time)`

---

## URL Routing

### HTML routes (`booking_project/urls.py` + `bookings/urls.py`)

```
/                           → home (bookings.views.home)
/accounts/register/         → register_view
/accounts/login/            → login_view
/accounts/logout/           → logout_view  [POST only]
/resources/                 → resource_list
/resources/<pk>/            → resource_detail
/bookings/                  → booking_list  [login required]
/bookings/new/              → booking_create  [login required]
/bookings/<pk>/             → booking_detail  [login required, owner only]
/bookings/<pk>/cancel/      → booking_cancel  [login required, owner only]
/admin/                     → Django admin
```

### API routes (`bookings/api_urls.py`, mounted at `/api/`)

```
GET  /api/                          → api_root
GET  /api/categories/               → ResourceCategoryListView
GET  /api/resources/                → ResourceListView
GET  /api/resources/<pk>/           → ResourceDetailView
GET  /api/bookings/                 → BookingListCreateView
POST /api/bookings/                 → BookingListCreateView
GET  /api/bookings/<pk>/            → BookingDetailView
POST /api/bookings/<pk>/cancel/     → booking_cancel_api
```

---

## Views Architecture

### HTML Views (`bookings/views.py`)
- All function-based views (FBVs)
- Authentication enforced with `@login_required` decorator
- Ownership enforced with `get_object_or_404(Booking, pk=pk, user=request.user)`
- Logout uses `@require_POST` to prevent CSRF-unsafe GET logout

### API Views (`bookings/api_views.py`)
- Mix of class-based (`generics.ListAPIView`, `generics.ListCreateAPIView`, `generics.RetrieveAPIView`) and `@api_view` function decorators
- All booking endpoints filter by `user=request.user` — users can only see/cancel their own bookings
- Resource endpoints are read-only and publicly accessible (`IsAuthenticatedOrReadOnly`)

---

## Forms (`bookings/forms.py`)

### `RegisterForm` (extends `UserCreationForm`)
- Adds `email`, `first_name`, `last_name` fields
- All inputs styled with `class="form-input"` for CSS variable theming

### `BookingForm` (ModelForm for `Booking`)
- Uses `datetime-local` HTML5 inputs
- `clean()` validates: end > start, start not in past, no resource conflict
- Only shows `is_active=True` resources in the resource dropdown

---

## Serializers (`bookings/serializers.py`)

- `ResourceCategorySerializer` — flat read
- `ResourceSerializer` — nested category (read), `category_id` (write)
- `BookingSerializer` — nested user + resource (read), `resource_id` (write); `create()` injects `request.user`; `validate()` mirrors form validation

---

## Templates

- All templates extend `templates/base.html`
- Tailwind CSS loaded via CDN Play script (`https://cdn.tailwindcss.com`)
- Custom CSS classes (`.btn`, `.card`, `.badge-*`, `.form-input`, `.alert-*`, `.nav-link`) defined in `static/css/theme.css`
- Colours use CSS custom properties (`var(--color-*)`) so they automatically adapt to light/dark mode
- WCAG 2.1 AA features:
  - Skip-to-content link (`.skip-link`) at top of every page
  - `aria-label` on all interactive elements
  - `aria-current="page"` on active nav links
  - `role="alert"` on error messages, `role="status"` on live regions
  - `<time datetime="...">` elements for machine-readable dates
  - `<dl>` / `<dt>` / `<dd>` for structured data
  - Sufficient colour contrast (verified against WCAG AA 4.5:1 ratio)

---

## Theme System

- `static/css/theme.css` — defines `:root` (light) and `[data-theme="dark"]` CSS variable sets
- `static/js/theme.js` — IIFE that:
  1. Reads `localStorage["booking-theme"]` or OS preference
  2. Sets `data-theme` on `<html>` before first paint (no flash)
  3. Wires up `#theme-toggle` button on `DOMContentLoaded`
- `base.html` loads `theme.js` in `<head>` (synchronously) to prevent FOUC

---

## Testing (`bookings/tests.py`)

Test classes:

| Class | What it tests |
|-------|--------------|
| `ResourceCategoryModelTest` | `__str__`, ordering |
| `ResourceModelTest` | `__str__`, `is_available` (no conflict, conflict, adjacent, exclude self, inactive) |
| `BookingModelTest` | `__str__`, `is_upcoming`, `duration_hours`, status choices |
| `AuthViewTest` | Register GET/POST, login GET/POST, logout POST, redirect if authenticated |
| `ResourceViewTest` | List (public, category filter), detail (public, 404 inactive, 404 nonexistent) |
| `BookingViewTest` | List (auth required, own only, status filter), create (GET, valid POST, conflict, past), detail (own, 404 other), cancel (GET confirm, POST cancel, 404 other, already cancelled) |
| `HomeViewTest` | Public home page |
| `APIResourceTest` | List (unauth, auth, filter), detail, category list |
| `APIBookingTest` | Auth required, own only, create (valid, conflict, bad times), detail (own, 404 other), cancel (success, already cancelled, 404 other), root, status filter |
| `BookingFormTest` | Valid form, end before start, inactive resource excluded |
| `RegisterFormTest` | Valid registration, password mismatch |

Run: `python manage.py test bookings`
Coverage: `coverage run manage.py test bookings && coverage report`

---

## Security Checklist

| Concern | Implementation |
|---------|---------------|
| CSRF | `{% csrf_token %}` in all forms; `CsrfViewMiddleware` enabled |
| SQL injection | ORM only — no `raw()` or `cursor.execute()` |
| XSS | Django auto-escapes template variables; `format_html()` in admin |
| Auth | `@login_required`, `get_object_or_404(..., user=request.user)` |
| Secrets | `django-environ` reads from `.env`; `.env` not committed |
| Clickjacking | `X-Frame-Options: DENY` |
| Session | `SESSION_COOKIE_HTTPONLY = True` |
| Passwords | Django PBKDF2 hashing with validators |

---

## Conventions

- **No raw SQL** — all queries via Django ORM
- **Function-based views** for HTML; class-based generics for API
- **CSS custom properties** for all colours — never hardcode hex in templates
- **`aria-*` attributes** on all interactive and status elements
- **`db_index=True`** on all ForeignKey fields and frequently filtered fields
- **`select_related()`** used in views to avoid N+1 queries
- **`update_fields`** used in `save()` calls that only change specific fields
