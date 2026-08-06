import json
from datetime import datetime
from django.shortcuts import render
from .models import Contact, MenuCategory, Order

# Home Page
def index(request):
    return render(request, "index.html")

# About Page
def about(request):
    return render(request, "about.html")

# Contact Page
def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        message = request.POST.get('message')

        contact_data = Contact(
            name=name,
            phone=phone,
            email=email,
            message=message,
            date=datetime.today()
        )
        contact_data.save()

        return render(request, "contact.html", {
            "success": "Your message has been sent successfully!"
        })

    return render(request, "contact.html")

# Services Page
def services(request):
    return render(request, "services.html")

# Orders Page
def orders(request):
    return render(request, "orders.html")

# Reservations Page
def reservations(request):
    return render(request, "reservations.html")

# Delivery Page
def delivery(request):
    return render(request, "deliverys.html")

# Admin Page
def admin(request):
    return render(request, "admin.html")

# Checkout Page (fixed)
def checkout(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        cart_data = request.POST.get("cart_data")

        cart = json.loads(cart_data)
        total = sum(float(item["price"]) for item in cart)

        # Save order to database
        order = Order(
            customer_name=name,
            phone=phone,
            total_amount=total
        )
        order.save()

        return render(request, "success.html", {"order": order})

    return render(request, "checkout.html")

# Menu Page
def menu(request):
    categories = MenuCategory.objects.prefetch_related("items").all()
    return render(request, "menu.html", {"categories": categories})
