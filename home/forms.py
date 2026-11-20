
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import MenuItem, CustomerProfile


# ---------------- CUSTOMER LOGIN FORM ----------------

class CustomLoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter email or username",
            "autofocus": True
        })
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter password"
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")

        # Allow login using email or username.
        user = User.objects.filter(
            email__iexact=username
        ).first()

        if user:
            return user.username

        return username


# ---------------- CUSTOMER SIGNUP FORM ----------------

class SignupForm(forms.Form):

    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your full name"
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your email"
        })
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter phone number"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Create password"
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm password"
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "This email is already registered."
            )

        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")

        if CustomerProfile.objects.filter(phone=phone).exists():
            raise ValidationError(
                "This phone number is already registered."
            )

        return phone

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error(
                "confirm_password",
                "Passwords do not match."
            )

        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error("password", error)

        return cleaned_data


# ---------------- ADMIN MENU ITEM FORM ----------------

class MenuItemForm(forms.ModelForm):

    class Meta:
        model = MenuItem

        fields = [
            "category",
            "name",
            "description",
            "price",
            "half_price",
            "full_price",
            "image_url",
        ]

        widgets = {
            "category": forms.Select(attrs={
                "class": "form-select"
            }),

            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter menu item name"
            }),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter item description"
            }),

            "price": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: 150 (leave blank for Half/Full pricing)"
            }),

            "half_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter half price",
                "step": "0.01"
            }),

            "full_price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter full price",
                "step": "0.01"
            }),

            "image_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://example.com/image.jpg"
            }),
        }

        labels = {
            "category": "Menu Category",
            "name": "Item Name",
            "description": "Description",
            "price": "Single Price (₹)",
            "half_price": "Half Price (₹)",
            "full_price": "Full Price (₹)",
            "image_url": "Image URL",
        }
