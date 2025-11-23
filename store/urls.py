from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.signin, name='signin'),
    path('signin_action/', views.signin_action, name='signin_action'),

    # OTP
    path('otp/', views.otp_check, name='otp_check'),          # OTP input form
    path('verify_otp/', views.verify_otp, name='verify_otp'), # POST to verify OTP

    # Signup
    path('signup/', views.signup, name='signup'),
    path('signup_action/', views.signup_action, name='signup_action'),

    # Products
    path('products/', views.products, name='products'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),

    # Cart
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_page, name='cart'),
    path('remove-item/<int:cart_id>/', views.remove_item, name='remove_item'),
    path('update-quantity/<int:cart_id>/<str:action>/', views.update_quantity, name='update_quantity'),

    # Buy Now / Orders
    path("buy/<int:product_id>/", views.buy_now, name="buy_now"),
    path("place-order/", views.place_order, name="place_order"),

    # Payment
    path('payment/<int:product_id>/', views.payment_buy_now, name='payment_buy_now'),
    path('payment/', views.payment_page, name='payment'),

    # Logout
    path('logout/', views.logout_view, name='logout'),
]
