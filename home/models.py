
from django.db import models
from django.contrib.auth.models import User


class Contact(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    message = models.TextField()
    date = models.DateField()

    def __str__(self):
        return self.name


class CustomerReview(models.Model):

    RATING_CHOICES = [
        (1, "1 Star"),
        (2, "2 Stars"),
        (3, "3 Stars"),
        (4, "4 Stars"),
        (5, "5 Stars"),
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Published", "Published"),
        ("Rejected", "Rejected"),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)

    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES
    )

    review = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.rating}/5"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.user.username


class MenuCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(
        MenuCategory,
        related_name="items",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Keep this field to support existing single-price and legacy entries.
    price = models.CharField(max_length=50, blank=True, default="")

    # Optional Half/Full pricing.
    half_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    full_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    image_url = models.URLField(blank=True)

    def __str__(self):
        if self.half_price is not None and self.full_price is not None:
            return f"{self.name} (Half: {self.half_price}, Full: {self.full_price})"

        return f"{self.name} ({self.price})"

    def clean(self):
        from django.core.exceptions import ValidationError

        has_half = self.half_price is not None
        has_full = self.full_price is not None

        if has_half != has_full:
            raise ValidationError(
                "Please enter both Half Price and Full Price."
            )

        if has_half and has_full and self.price:
            raise ValidationError(
                "Use either a single price or Half/Full prices, not both."
            )

        if not self.price and not (has_half and has_full):
            raise ValidationError(
                "Enter a single price or both Half and Full prices."
            )


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default="Preparing")
    estimated_delivery = models.CharField(
        max_length=50,
        default="30 - 40 Minutes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_id} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )
    item_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)

    # The actual amount charged for this item.
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # For example: Regular, Half, or Full.
    variant = models.CharField(max_length=20, blank=True, default="")

    def __str__(self):
        return f"{self.item_name} × {self.quantity}"


class LoginOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.username}"
