from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
import re
from .utils import generate_otp, send_sms_otp
from .models import Product, Review, Cart, Order
from django.shortcuts import render, redirect, get_object_or_404

# ---------------- LOGIN PAGE ----------------
def signin(request):
    if request.user.is_authenticated:
        return redirect('products')
    return render(request, "signin.html")


# ---------------- SIGNIN ACTION ----------------
def signin_action(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")

        if not identifier:
            messages.error(request, "Please enter email or mobile number")
            return redirect("signin")

        # Identify email or mobile
        is_mobile = re.fullmatch(r"\d{10}", identifier)
        is_email = re.fullmatch(r"[^@]+@[^@]+\.[^@]+", identifier)

        if not (is_mobile or is_email):
            messages.error(request, "Invalid email or mobile number")
            return redirect("signin")

        # Fetch user based on identifier
        if is_email:
            user = User.objects.filter(email=identifier).first()
        else:
            user = User.objects.filter(username=identifier).first()

        if not user:
            messages.error(request, "User not found")
            return redirect("signin")

        # Generate OTP and store in session
        otp = generate_otp()
        request.session["otp"] = otp
        request.session["identifier"] = identifier

        # Send OTP via email or SMS
        if is_email:
            send_mail(
                "Your Login OTP",
                f"Your OTP is {otp}",
                settings.EMAIL_HOST_USER,
                [identifier],
            )
        else:
            send_sms_otp(identifier, otp)

        messages.success(request, "OTP sent successfully")
        return redirect("otp_check")

    return redirect("signin")


# ---------------- OTP PAGE ----------------
def otp_check(request):
    return render(request, 'verify_otp.html')


# ---------------- VERIFY OTP ----------------
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        actual_otp = request.session.get("otp")
        identifier = request.session.get("identifier")

        if entered_otp == actual_otp:
            # Get the user safely
            if re.fullmatch(r"[^@]+@[^@]+\.[^@]+", identifier):
                user = User.objects.filter(email=identifier).first()
            else:
                user = User.objects.filter(username=identifier).first()

            if not user:
                messages.error(request, "User not found")
                return redirect("signin")

            # Set backend to avoid ValueError
            from django.contrib.auth import get_backends
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"

            # Log in the user
            auth_login(request, user)

            # Clear OTP from session
            request.session.pop("otp", None)
            request.session.pop("identifier", None)

            messages.success(request, "OTP Verified Successfully")
            return redirect("products")

        messages.error(request, "Invalid OTP")
        return redirect("otp_check")

    return redirect("otp_check")

# ---------------- LOGOUT ----------------
@login_required
def logout_view(request):
    auth_logout(request)
    return redirect("signin")



def logout_view(request):
    auth_logout(request)
    return redirect("signin")


# -------------------- PRODUCTS --------------------

def products(request):
    search_query = request.GET.get('q', '')

    products = Product.objects.all()

    if search_query:
        products = products.filter(name__icontains=search_query)

    context = {
        'products': products,
    }
    return render(request, 'home.html', context)




def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)

    return render(request, "product_details.html", {
        "product": product,
        "reviews": reviews,
    })


# -------------------- CART --------------------

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    cart_item, created = Cart.objects.get_or_create(
        user=user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, "Item quantity updated.")
    else:
        messages.success(request, "Item added to cart.")

    return redirect("cart")


@login_required
def cart_page(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.sub_total for item in cart_items)

    return render(request, "cart.html", {
        "cart_items": cart_items,
        "total_price": total_price
    })


@login_required
def remove_item(request, cart_id):
    Cart.objects.get(id=cart_id).delete()
    return redirect('cart')


@login_required
def update_quantity(request, cart_id, action):
    cart_item = Cart.objects.get(id=cart_id)

    if action == "increase":
        cart_item.quantity += 1
    elif action == "decrease" and cart_item.quantity > 1:
        cart_item.quantity -= 1

    cart_item.save()
    return redirect('cart')


# -------------------- BUY NOW --------------------

def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        product=product,
        quantity=1,
        total_price=product.price,
        status="PENDING"
    )

    return redirect("checkout", order_id=order.id)


# -------------------- SIGNUP --------------------

def signup(request):
    return render(request, "signup.html")


def signup_action(request):
    if request.method == "POST":
        name = request.POST.get("name")
        mobile = request.POST.get("mobile")
        password = request.POST.get("password")

        if not name or not mobile or not password:
            messages.error(request, "All fields are required")
            return redirect("signup")

        if not re.fullmatch(r"\d{10}", mobile):
            messages.error(request, "Enter a valid 10-digit mobile number")
            return redirect("signup")

        if User.objects.filter(username=mobile).exists():
            messages.error(request, "Mobile number already registered")
            return redirect("signup")

        User.objects.create_user(
            username=mobile,
            password=password,
            first_name=name
        )

        messages.success(request, "Account created successfully! Please sign in.")
        return redirect("signin")

    return redirect("signup")


@login_required
def place_order(request):
    user = request.user

    # BUY NOW ORDER
    if "buy_now_product" in request.session:
        product_id = request.session["buy_now_product"]
        product = Product.objects.get(id=product_id)

        Order.objects.create(
            user=user,
            product=product,
            quantity=1,
            total_price=product.price,
            status="CONFIRMED"
        )

        del request.session["buy_now_product"]

        messages.success(request, "Order placed successfully!")
        return redirect("products")

    # CART ORDER
    cart_items = Cart.objects.filter(user=user)

    for item in cart_items:
        Order.objects.create(
            user=user,
            product=item.product,
            quantity=item.quantity,
            total_price=item.sub_total,
            status="CONFIRMED"
        )

    cart_items.delete()

    messages.success(request, "Order placed successfully!")
    return redirect("products")


def payment_buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "payment.html", {"product": product})
@login_required
def payment_page(request):

    cart_items = None
    total_price = None
    product_name = None
    amount = None

    # ---- CASE 1: Coming from CART ----
    if request.GET.get("from_cart") == "1":
        cart_items = Cart.objects.filter(user=request.user)
        total_price = sum(item.sub_total for item in cart_items)

    # ---- CASE 2: Coming from BUY NOW ----
    if request.GET.get("product_id"):
        product_id = request.GET.get("product_id")
        product = Product.objects.get(id=product_id)
        product_name = product.name
        amount = product.price

    context = {
        "cart_items": cart_items,
        "total_price": total_price,
        "product_name": product_name,
        "amount": amount
    }

    return render(request, "payment.html", context)

