from django.contrib import admin
from .models import Contact, MenuCategory, MenuItem, Order

# Contact
admin.site.register(Contact)

# Menu Category
@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)

# Menu Item
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    list_filter = ("category",)
    search_fields = ("name",)

# Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "customer_name", "phone", "total_amount", "status", "created_at")
    search_fields = ("customer_name", "phone")
    list_filter = ("status", "created_at")
