from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    path("", views.index, name='home'),
    path("about/", views.about, name='about'),
    path("contact/", views.contact, name='contact'),
    path("services/", views.services, name='services'),
    path("menu/", views.menu, name='menu'),
    path("orders/", views.orders, name='orders'),
    path("reservations/", views.reservations, name='reservations'),
    path("delivery/", views.delivery, name='delivery'),
    path("checkout/", views.checkout, name='checkout'),
]

