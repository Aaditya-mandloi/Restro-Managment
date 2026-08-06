from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=12)
    email = models.EmailField()
    message = models.TextField()
    date = models.DateField()

class MenuCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.CharField(max_length=50)  # keep CharField for ranges like "70/130"
    image_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.price})"

class Order(models.Model):   # <-- now correctly at top level
    order_id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default="Preparing")
    estimated_delivery = models.CharField(max_length=50, default="30 - 40 Minutes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_id} - {self.customer_name}"
