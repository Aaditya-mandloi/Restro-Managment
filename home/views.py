
import json
from calendar import monthcalendar
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Sum, Q, Count, Avg, Max
from django.db import transaction
from django.core.paginator import Paginator

from .models import (
    Contact,
    CustomerReview,
    MenuCategory,
    MenuItem,
    Order,
    OrderItem,
    CustomerProfile,
)

from .forms import (
    CustomLoginForm,
    SignupForm,
    MenuItemForm,
)


# ---------------- ORDER STATUS OPTIONS ----------------

ORDER_STATUSES = [
    "Pending",
    "Confirmed",
    "Preparing",
    "Out for Delivery",
    "Delivered",
    "Cancelled",
]


# ---------------- HOME PAGE ----------------

def index(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        message = request.POST.get("message")

        Contact.objects.create(
            name=name,
            phone=phone,
            email=email,
            message=message,
            date=datetime.today()
        )

        return render(request, "contact.html", {
            "success": "Your message has been sent successfully!"
        })

    return render(request, "contact.html")


def services(request):
    return render(request, "services.html")


def orders(request):
    return render(request, "orders.html")


def reservations(request):
    return render(request, "reservations.html")


def delivery(request):
    return render(request, "deliverys.html")


# ---------------- CUSTOMER CHECKOUT ----------------

@login_required
def checkout(request):
    if request.method == "POST":
        try:
            name = request.POST.get("name")
            phone = request.POST.get("phone")
            address = request.POST.get("address")
            cart_data = request.POST.get("cart_data", "[]")

            cart = json.loads(cart_data)

            if not isinstance(cart, list) or not cart:
                return render(request, "checkout.html", {
                    "error": "Your cart is empty or invalid."
                })

            total = Decimal("0.00")

            for item in cart:
                quantity = int(item.get("quantity", 1))
                price = Decimal(str(item["price"]))

                if quantity < 1 or price < 0:
                    raise ValueError("Invalid cart item")

                total += price * quantity

            order = Order.objects.create(
                customer=request.user,
                customer_name=name,
                phone=phone,
                address=address,
                total_amount=total
            )

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    item_name=item["name"],
                    quantity=int(item.get("quantity", 1)),
                    price=Decimal(str(item["price"])),
                    variant=item.get("variant", "")
                )

            return render(request, "success.html", {
                "order": order
            })

        except (
            ValueError,
            TypeError,
            KeyError,
            InvalidOperation,
            json.JSONDecodeError
        ):
            return render(request, "checkout.html", {
                "error": "There was a problem processing your order. Please check your cart."
            })

    return render(request, "checkout.html")


# ---------------- MENU PAGE ----------------

def menu(request):
    categories = MenuCategory.objects.prefetch_related("items").all()

    return render(request, "menu.html", {
        "categories": categories
    })


# ---------------- CUSTOMER ORDER HISTORY ----------------

@login_required
def order_history(request):
    user_orders = (
        Order.objects
        .filter(customer=request.user)
        .order_by("-created_at")
        .prefetch_related("items")
    )

    return render(request, "order_history.html", {
        "orders": user_orders
    })


# ---------------- CUSTOMER LOGIN ----------------

class CustomLoginView(LoginView):
    template_name = "login.html"
    authentication_form = CustomLoginForm
    redirect_authenticated_user = True


# ---------------- CUSTOMER SIGNUP ----------------

def signup(request):
    if request.user.is_authenticated:
        return redirect("order_history")

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            phone = form.cleaned_data["phone"]
            password = form.cleaned_data["password"]

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name
            )

            CustomerProfile.objects.create(
                user=user,
                phone=phone
            )

            customer_group, created = Group.objects.get_or_create(
                name="Customer"
            )

            user.groups.add(customer_group)

            login(request, user)

            return redirect("order_history")

    else:
        form = SignupForm()

    return render(request, "signup.html", {
        "form": form
    })


# ---------------- ADMIN AUTHENTICATION ----------------

def is_admin_user(user):
    return (
        user.is_authenticated
        and user.is_active
        and user.is_staff
        and (
            user.is_superuser
            or user.groups.filter(name="Admin").exists()
        )
    )


class AdminLoginView(LoginView):
    template_name = "admin/login.html"
    authentication_form = CustomLoginForm
    redirect_authenticated_user = False

    def form_valid(self, form):
        user = form.get_user()

        if not is_admin_user(user):
            messages.error(
                self.request,
                "You do not have permission to access the admin panel."
            )
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("admin_dashboard")


# ---------------- ADMIN DASHBOARD ----------------

@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
def admin_dashboard(request):

    total_orders = Order.objects.count()

    total_customers = CustomerProfile.objects.count()

    total_menu_items = MenuItem.objects.count()

    total_revenue = (
        Order.objects.aggregate(total=Sum("total_amount"))["total"]
        or Decimal("0.00")
    )

    pending_orders = Order.objects.filter(
        status__in=["Pending", "Confirmed", "Preparing"]
    ).count()

    recent_orders = (
        Order.objects
        .select_related("customer")
        .prefetch_related("items")
        .order_by("-created_at")[:5]
    )

    context = {
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_menu_items": total_menu_items,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
        "recent_orders": recent_orders,
    }

    return render(request, "admin/dashboard.html", context)


# ---------------- ADMIN ORDER MANAGEMENT ----------------

@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
def admin_orders(request):

    today = timezone.localdate()

    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))

        if month < 1 or month > 12 or year < 2000 or year > 2100:
            raise ValueError

    except (ValueError, TypeError):
        year = today.year
        month = today.month

    calendar_days = monthcalendar(year, month)

    monthly_orders = Order.objects.filter(
        created_at__year=year,
        created_at__month=month
    )

    daily_sales = (
        monthly_orders
        .values("created_at__date")
        .annotate(
            order_count=Count("order_id"),
            total_sales=Sum("total_amount")
        )
    )

    daily_data = {
        item["created_at__date"]: item
        for item in daily_sales
    }

    calendar_data = []

    for week in calendar_days:
        week_data = []

        for day in week:
            if day == 0:
                week_data.append(None)
                continue

            selected_day = date(year, month, day)
            data = daily_data.get(selected_day, {})

            week_data.append({
                "day": day,
                "date": selected_day,
                "order_count": data.get("order_count", 0),
                "total_sales": data.get("total_sales") or Decimal("0.00"),
            })

        calendar_data.append(week_data)

    selected_date_string = request.GET.get("date", "")

    try:
        selected_date = (
            date.fromisoformat(selected_date_string)
            if selected_date_string
            else today
        )
    except ValueError:
        selected_date = today

    if selected_date.year != year or selected_date.month != month:
        selected_date = date(year, month, 1)

    day_orders = Order.objects.filter(
        created_at__date=selected_date
    )

    daily_total = (
        day_orders.aggregate(total=Sum("total_amount"))["total"]
        or Decimal("0.00")
    )

    daily_order_count = day_orders.count()

    selected_orders = (
        day_orders
        .select_related("customer")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    search_query = request.GET.get("search", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search_query:
        search_filter = (
            Q(customer_name__icontains=search_query)
            | Q(phone__icontains=search_query)
        )

        if search_query.isdigit():
            search_filter |= Q(order_id=int(search_query))

        selected_orders = selected_orders.filter(search_filter)

    if selected_status in ORDER_STATUSES:
        selected_orders = selected_orders.filter(
            status=selected_status
        )

    previous_month = (
        date(year - 1, 12, 1) if month == 1
        else date(year, month - 1, 1)
    )

    next_month = (
        date(year + 1, 1, 1) if month == 12
        else date(year, month + 1, 1)
    )

    context = {
        "orders": selected_orders,
        "search_query": search_query,
        "selected_status": selected_status,
        "order_statuses": ORDER_STATUSES,

        "calendar_data": calendar_data,
        "calendar_year": year,
        "calendar_month": month,
        "calendar_month_name": date(year, month, 1).strftime("%B"),

        "selected_date": selected_date,
        "daily_total": daily_total,
        "daily_order_count": daily_order_count,

        "previous_month": previous_month,
        "next_month": next_month,
    }

    return render(request, "admin/orders.html", context)


# ---------------- ADMIN SALES REPORTS ----------------

@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
def admin_sales_reports(request):

    today = timezone.localdate()
    default_start = today.replace(day=1)

    start_date_string = request.GET.get(
        "start_date", default_start.isoformat()
    )
    end_date_string = request.GET.get(
        "end_date", today.isoformat()
    )

    try:
        start_date = date.fromisoformat(start_date_string)
        end_date = date.fromisoformat(end_date_string)

        if start_date > end_date:
            start_date, end_date = end_date, start_date

    except (ValueError, TypeError):
        start_date = default_start
        end_date = today

    report_orders = Order.objects.filter(
        created_at__date__range=(start_date, end_date)
    ).exclude(status="Cancelled")

    total_sales = (
        report_orders.aggregate(total=Sum("total_amount"))["total"]
        or Decimal("0.00")
    )

    total_orders = report_orders.count()

    average_order_value = (
        total_sales / total_orders
        if total_orders > 0
        else Decimal("0.00")
    )

    daily_sales = (
        report_orders
        .values("created_at__date")
        .annotate(
            order_count=Count("order_id"),
            total_sales=Sum("total_amount")
        )
        .order_by("created_at__date")
    )

    context = {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "average_order_value": average_order_value,
        "daily_sales": daily_sales,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(
        request,
        "admin/sales_reports.html",
        context
    )


# ---------------- UPDATE ORDER STATUS ----------------

@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
@require_POST
def admin_update_order(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    new_status = request.POST.get("status", "").strip()
    estimated_delivery = request.POST.get(
        "estimated_delivery", ""
    ).strip()

    if new_status not in ORDER_STATUSES:
        messages.error(request, "Invalid order status.")
        return redirect("admin_orders")

    order.status = new_status

    if estimated_delivery:
        if len(estimated_delivery) > 50:
            messages.error(
                request,
                "Estimated delivery time is too long."
            )
            return redirect("admin_orders")

        order.estimated_delivery = estimated_delivery

    order.save(
        update_fields=["status", "estimated_delivery"]
    )

    messages.success(
        request,
        f"Order #{order.order_id} updated successfully."
    )

    return redirect("admin_orders")


# ---------------- ADMIN LOGOUT ----------------

@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
@require_POST
def admin_logout(request):
    logout(request)
    return redirect("admin_login")


# ---------------- CUSTOMER LOGOUT ----------------

@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect("home")


# ---------------- ADMIN MENU MANAGEMENT ----------------

@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
def admin_menu(request):

    menu_items = (
        MenuItem.objects.select_related("category")
        .order_by("category__name", "name")
    )

    search_query = request.GET.get("search", "").strip()
    selected_category = request.GET.get("category", "").strip()

    if search_query:
        menu_items = menu_items.filter(name__icontains=search_query)

    if selected_category.isdigit():
        menu_items = menu_items.filter(category_id=int(selected_category))

    categories = (
        MenuCategory.objects
        .annotate(item_count=Count("items"))
        .order_by("name")
    )

    context = {
        "menu_items": menu_items,
        "categories": categories,
        "search_query": search_query,
        "selected_category": selected_category,
    }

    return render(request, "admin/menu.html", context)


@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
@require_POST
def admin_category_add(request):

    category_name = request.POST.get("name", "").strip()

    if not category_name:
        messages.error(request, "Category name cannot be empty.")

    elif len(category_name) > 100:
        messages.error(request, "Category name cannot exceed 100 characters.")

    elif MenuCategory.objects.filter(name__iexact=category_name).exists():
        messages.error(request, "This category already exists.")

    else:
        MenuCategory.objects.create(name=category_name)
        messages.success(
            request,
            f"Category '{category_name}' added successfully!"
        )

    return redirect("admin_menu")


@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
@require_POST
def admin_category_delete(request, category_id):

    with transaction.atomic():
        category = get_object_or_404(
            MenuCategory.objects.select_for_update(),
            id=category_id
        )

        if category.items.exists():
            messages.error(
                request,
                f"Cannot delete '{category.name}' because it contains menu items. "
                "Move or delete those items first."
            )
        else:
            category_name = category.name
            category.delete()
            messages.success(
                request,
                f"Category '{category_name}' deleted successfully!"
            )

    return redirect("admin_menu")


@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
def admin_menu_add(request):

    if request.method == "POST":
        form = MenuItemForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Menu item added successfully!")
            return redirect("admin_menu")
    else:
        form = MenuItemForm()

    return render(request, "admin/menu_form.html", {
        "form": form,
        "page_title": "Add Menu Item",
    })


@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
def admin_menu_edit(request, item_id):

    menu_item = get_object_or_404(MenuItem, id=item_id)

    if request.method == "POST":
        form = MenuItemForm(request.POST, instance=menu_item)

        if form.is_valid():
            form.save()
            messages.success(request, "Menu item updated successfully!")
            return redirect("admin_menu")
    else:
        form = MenuItemForm(instance=menu_item)

    return render(request, "admin/menu_form.html", {
        "form": form,
        "page_title": "Edit Menu Item",
    })


@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
@require_POST
def admin_menu_delete(request, item_id):

    menu_item = get_object_or_404(MenuItem, id=item_id)
    menu_item.delete()

    messages.success(request, "Menu item deleted successfully!")
    return redirect("admin_menu")


# ---------------- ADMIN CUSTOMER MANAGEMENT ----------------

@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
def admin_customers(request):

    today = timezone.localdate()
    month_start = today.replace(day=1)

    customer_list = CustomerProfile.objects.select_related(
        "user"
    ).annotate(
        total_orders=Count(
            "user__order",
            filter=~Q(user__order__status="Cancelled"),
            distinct=True
        ),
        total_spent=Sum(
            "user__order__total_amount",
            filter=~Q(user__order__status="Cancelled")
        ),
        last_order=Max(
            "user__order__created_at",
            filter=~Q(user__order__status="Cancelled")
        )
    )

    search_query = request.GET.get("q", "").strip()

    if search_query:
        customer_list = customer_list.filter(
            Q(user__username__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(phone__icontains=search_query)
        )

    customer_type = request.GET.get("type", "")

    if customer_type == "new":
        customer_list = customer_list.filter(
            user__date_joined__date__gte=month_start
        )

    elif customer_type == "repeat":
        customer_list = customer_list.filter(
            total_orders__gt=1
        )

    sort_by = request.GET.get("sort", "newest")

    sort_options = {
        "newest": "-user__date_joined",
        "oldest": "user__date_joined",
        "spending": "-total_spent",
        "orders": "-total_orders",
        "recent_order": "-last_order",
    }

    customer_list = customer_list.order_by(
        sort_options.get(sort_by, "-user__date_joined")
    )

    total_customers = CustomerProfile.objects.count()

    new_customers = CustomerProfile.objects.filter(
        user__date_joined__date__gte=month_start
    ).count()

    repeat_customers = CustomerProfile.objects.annotate(
        order_count=Count(
            "user__order",
            filter=~Q(user__order__status="Cancelled"),
            distinct=True
        )
    ).filter(order_count__gt=1).count()

    spending_data = CustomerProfile.objects.annotate(
        customer_spending=Sum(
            "user__order__total_amount",
            filter=~Q(user__order__status="Cancelled")
        )
    ).aggregate(
        average_spending=Avg("customer_spending")
    )

    average_spending = (
        spending_data["average_spending"] or Decimal("0.00")
    )

    paginator = Paginator(customer_list, 10)
    page_number = request.GET.get("page")
    customers = paginator.get_page(page_number)

    context = {
        "customers": customers,
        "total_customers": total_customers,
        "new_customers": new_customers,
        "repeat_customers": repeat_customers,
        "average_spending": average_spending,
        "search_query": search_query,
        "customer_type": customer_type,
        "sort_by": sort_by,
    }

    return render(
        request,
        "admin/customers.html",
        context
    )


# ---------------- ADMIN CUSTOMER MESSAGES & REVIEWS ----------------

@login_required
@user_passes_test(is_admin_user, login_url="admin_login")
def admin_customer_messages(request):

    reviews = CustomerReview.objects.select_related(
        "customer"
    ).order_by("-created_at")

    total_reviews = reviews.count()

    average_rating = reviews.aggregate(
        average=Avg("rating")
    )["average"] or 0

    pending_reviews = reviews.filter(
        status="Pending"
    ).count()

    published_reviews = reviews.filter(
        status="Published"
    ).count()

    context = {
        "reviews": reviews,
        "total_reviews": total_reviews,
        "average_rating": average_rating,
        "pending_reviews": pending_reviews,
        "published_reviews": published_reviews,
    }

    return render(
        request,
        "admin/customer_messages.html",
        context
    )
