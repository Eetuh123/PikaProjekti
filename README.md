# BookIt — Django Resource Booking System

A full-featured resource booking/reservation system built with Django 4.2, Django REST Framework, and Tailwind CSS.

---

## Features

- **User authentication** — register, login, logout with secure password hashing
- **Resource management** — browse resources by category, view availability
- **Booking CRUD** — create, view, and cancel bookings with conflict detection
- **REST API** — full DRF API for resources and bookings
- **Admin panel** — Django admin with rich list views and filters
- **Light/dark mode** — CSS-variable-based theme toggle, persisted in `localStorage`
- **WCAG 2.1 AA** — skip links, ARIA labels, focus rings, semantic HTML, sufficient contrast
- **Responsive design** — mobile-first with Tailwind CSS (CDN)
- **Security** — CSRF protection, ORM-only queries, XSS prevention, `django-environ` for secrets

---

## Requirements

- Python 3.11+
- PostgreSQL 14+ (or SQLite for development)
- pip

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repo-url>
cd PikaProjekti
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install django==4.2.* djangorestframework django-environ psycopg2-binary Pillow coverage
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

`.env` contents:

```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://bookinguser:bookingpass@localhost:5432/bookingdb
ALLOWED_HOSTS=localhost,127.0.0.1
```

For **SQLite** (no PostgreSQL needed):

```
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Set up the database

**PostgreSQL** (optional — skip for SQLite):

```sql
CREATE USER bookinguser WITH PASSWORD 'bookingpass';
CREATE DATABASE bookingdb OWNER bookinguser;
```

**Run migrations:**

```bash
python manage.py migrate
```

### 6. Load seed data

```bash
python manage.py loaddata bookings/fixtures/initial_data.json
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000)

---

## Project Structure

```
PikaProjekti/
├── booking_project/        # Django project settings & root URLs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── bookings/               # Main application
│   ├── models.py           # ResourceCategory, Resource, Booking
│   ├── views.py            # HTML views (auth, resources, bookings)
│   ├── api_views.py        # DRF API views
│   ├── serializers.py      # DRF serializers
│   ├── forms.py            # Django forms
│   ├── admin.py            # Admin configuration
│   ├── urls.py             # App URL patterns
│   ├── api_urls.py         # API URL patterns
│   ├── tests.py            # Unit tests
│   └── fixtures/
│       └── initial_data.json
├── templates/              # Django templates
│   ├── base.html
│   ├── home.html
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
├── static/
│   ├── css/theme.css       # CSS variables (light/dark mode)
│   └── js/theme.js         # Theme toggle script
├── .env                    # Environment variables (not committed)
├── .env.example            # Example env file
├── manage.py
├── README.md
├── TODO.md
└── AGENTS.md
```

---

## Running Tests

```bash
# Run all tests
python manage.py test bookings

# With coverage report
coverage run manage.py test bookings
coverage report
coverage html   # generates htmlcov/index.html
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/` | API overview |
| GET | `/api/categories/` | List resource categories |
| GET | `/api/resources/` | List active resources |
| GET | `/api/resources/<id>/` | Resource detail |
| GET | `/api/bookings/` | List own bookings |
| POST | `/api/bookings/` | Create a booking |
| GET | `/api/bookings/<id>/` | Booking detail |
| POST | `/api/bookings/<id>/cancel/` | Cancel a booking |

**Query parameters:**
- `/api/resources/?category=<id>` — filter by category
- `/api/resources/?search=<term>` — search by name/location
- `/api/bookings/?status=confirmed|cancelled|pending` — filter by status

---

## Web Routes

| URL | Description |
|-----|-------------|
| `/` | Home / landing page |
| `/accounts/register/` | User registration |
| `/accounts/login/` | Login |
| `/accounts/logout/` | Logout (POST) |
| `/resources/` | Browse resources |
| `/resources/<id>/` | Resource detail |
| `/bookings/` | My bookings |
| `/bookings/new/` | Create booking |
| `/bookings/<id>/` | Booking detail |
| `/bookings/<id>/cancel/` | Cancel booking |
| `/admin/` | Django admin |

---

## Security Notes

- All secrets are loaded from `.env` via `django-environ` — never commit `.env`
- CSRF protection is enabled on all state-changing forms
- All database queries use the Django ORM — no raw SQL
- Passwords are hashed with Django's PBKDF2 algorithm
- `X-Frame-Options: DENY` header is set
- Session cookies are `HttpOnly`

---

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | — (required) |
| `DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | Database connection URL | `sqlite:///db.sqlite3` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
