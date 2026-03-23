"""
Forms for the bookings application.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Booking, Resource


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-input", "placeholder": "you@example.com", "autocomplete": "email"}
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-input", "placeholder": "First name", "autocomplete": "given-name"}
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-input", "placeholder": "Last name", "autocomplete": "family-name"}
        ),
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-input"
        self.fields["username"].widget.attrs.update({"placeholder": "Username", "autocomplete": "username"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Password", "autocomplete": "new-password"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm password", "autocomplete": "new-password"})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-input"


class BookingForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-input"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-input"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Booking
        fields = ("resource", "title", "notes", "start_time", "end_time")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "Booking title"}),
            "notes": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "Optional notes…"}),
            "resource": forms.Select(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resource"].queryset = Resource.objects.filter(is_active=True).select_related("category")

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        resource = cleaned_data.get("resource")

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
            if start_time < timezone.now():
                raise forms.ValidationError("Start time cannot be in the past.")
            if resource:
                exclude_id = self.instance.pk if self.instance.pk else None
                if not resource.is_available(start_time, end_time, exclude_booking_id=exclude_id):
                    raise forms.ValidationError(
                        f'"{resource.name}" is already booked for the selected time slot. '
                        "Please choose a different time or resource."
                    )

        return cleaned_data