
from django.urls import path
from home import views


urlpatterns = [
    # Main pages
    path("", views.index, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("services/", views.services, name="services"),

    # Restaurant pages
    path("menu/", views.menu, name="menu"),
    path("orders/", views.orders, name="orders"),
    path("reservations/", views.reservations, name="reservations"),
    path("delivery/", views.delivery, name="delivery"),

    # Customer ordering
    path("checkout/", views.checkout, name="checkout"),
    path("order_history/", views.order_history, name="order_history"),

    # Customer authentication
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    # Admin authentication and dashboard
    path("admin-panel/login/", views.AdminLoginView.as_view(), name="admin_login"),
    path("admin-panel/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/logout/", views.admin_logout, name="admin_logout"),

    # Admin orders
    path("admin-panel/orders/", views.admin_orders, name="admin_orders"),
    path(
        "admin-panel/orders/update/<int:order_id>/",
        views.admin_update_order,
        name="admin_update_order"
    ),

    # Admin menu
    path("admin-panel/menu/", views.admin_menu, name="admin_menu"),
    path("admin-panel/menu/add/", views.admin_menu_add, name="admin_menu_add"),
    path(
        "admin-panel/menu/edit/<int:item_id>/",
        views.admin_menu_edit,
        name="admin_menu_edit"
    ),
    path(
        "admin-panel/menu/delete/<int:item_id>/",
        views.admin_menu_delete,
        name="admin_menu_delete"
    ),

    # Admin categories
    path(
        "admin-panel/category/add/",
        views.admin_category_add,
        name="admin_category_add"
    ),
    path(
        "admin-panel/category/delete/<int:category_id>/",
        views.admin_category_delete,
        name="admin_category_delete"
    ),

    # Admin reports, customers and messages
    path(
        "admin-panel/sales-reports/",
        views.admin_sales_reports,
        name="admin_sales_reports"
    ),
    path(
        "admin-panel/customers/",
        views.admin_customers,
        name="admin_customers"
    ),
    path(
        "admin-panel/customer-messages/",
        views.admin_customer_messages,
        name="admin_customer_messages"
    ),
]
