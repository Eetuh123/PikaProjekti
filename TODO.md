# TODO — Potential Future Improvements

This document lists features and improvements that could be added to BookIt in future iterations.

---

## High Priority

### Functionality
- [ ] **Booking edit** — Allow users to modify an existing confirmed booking (change time, notes)
- [ ] **Recurring bookings** — Support weekly/daily recurring reservations
- [ ] **Email notifications** — Send confirmation and cancellation emails via Django's email backend
- [ ] **Calendar view** — Visual calendar (e.g. FullCalendar.js) showing resource availability
- [ ] **iCal export** — Export bookings as `.ics` files for calendar apps

### Security & Auth
- [ ] **Password reset** — Implement forgot-password / reset-password flow
- [ ] **Email verification** — Require email confirmation on registration
- [ ] **OAuth / SSO** — Add social login (Google, Microsoft) via `django-allauth`
- [ ] **Rate limiting** — Throttle login attempts and API endpoints
- [ ] **Two-factor authentication (2FA)** — Add TOTP support via `django-otp`

---

## Medium Priority

### UX / Frontend
- [ ] **Real-time availability** — Use HTMX or WebSockets to show live availability without page reload
- [ ] **Booking duration picker** — Replace raw datetime inputs with a visual time-slot picker
- [ ] **Search & filter** — Full-text search across resources and bookings
- [ ] **Pagination** — Add pagination to booking and resource lists
- [ ] **Toast notifications** — Replace Django messages with animated toast popups
- [ ] **Print-friendly booking confirmation** — Printable booking receipt page

### Admin & Management
- [ ] **Resource images** — Allow admins to upload photos for resources
- [ ] **Booking approval workflow** — Optional admin approval before a booking is confirmed
- [ ] **Bulk operations** — Admin bulk cancel/approve bookings
- [ ] **Usage analytics dashboard** — Charts showing resource utilisation over time
- [ ] **Waitlist** — Allow users to join a waitlist when a resource is fully booked

### API
- [ ] **OpenAPI / Swagger docs** — Auto-generate API docs with `drf-spectacular`
- [ ] **JWT authentication** — Add token-based auth for mobile/SPA clients via `djangorestframework-simplejwt`
- [ ] **Webhook support** — Notify external systems on booking events
- [ ] **API versioning** — Version the API (e.g. `/api/v1/`)

---

## Low Priority / Nice to Have

### Infrastructure
- [ ] **Docker Compose** — Add `docker-compose.yml` for one-command local setup
- [ ] **CI/CD pipeline** — GitHub Actions workflow for tests and linting
- [ ] **Production deployment guide** — Nginx + Gunicorn + PostgreSQL setup docs
- [ ] **Environment-specific settings** — Split `settings.py` into `base`, `dev`, `prod`
- [ ] **Static file CDN** — Configure `django-storages` + S3/CloudFront for static/media files
- [ ] **Sentry integration** — Error tracking in production

### Testing
- [ ] **Selenium / Playwright E2E tests** — Browser-level tests for critical user flows
- [ ] **Factory Boy** — Replace manual test helpers with `factory_boy` factories
- [ ] **Hypothesis** — Property-based testing for booking conflict logic
- [ ] **Performance tests** — Load testing with Locust

### Accessibility & i18n
- [ ] **Internationalisation (i18n)** — Add Finnish and other language translations
- [ ] **High-contrast mode** — Additional CSS theme for users who need higher contrast
- [ ] **Screen reader testing** — Formal audit with NVDA / VoiceOver

### Features
- [ ] **Resource tags** — Flexible tagging system (e.g. "projector", "wheelchair accessible")
- [ ] **Capacity enforcement** — Prevent overbooking based on attendee count vs. capacity
- [ ] **User profile page** — Let users update their name, email, and notification preferences
- [ ] **Booking comments/notes thread** — Allow back-and-forth notes between user and admin
- [ ] **Public resource calendar** — Embeddable public calendar for a resource
