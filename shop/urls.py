from django.urls import path
from . import views


urlpatterns = [
    # When the URL is empty, call the 'index' function in the views module and name it 'index'
    path('', views.index, name='index'),
    
    # When the URL matches the format 'categories/<str:category>', call the 'category_view' function in the views module and name it 'categories'
    path('categories/<str:category>', views.category_view, name='categories'),

    # When the URL matches 'login', call the 'login' function in the views module and name it 'login'
    path('login', views.login, name='login'),

    # When the URL matches 'register', call the 'register' function in the views module and name it 'register'
    path('register', views.register, name='register'),

    # When the URL matches 'logout', call the 'logout' function in the views module and name it 'logout'
    path('logout', views.logout, name='logout'),

    # When the URL matches 'create-store', call the 'create_store' function in the views module and name it 'create-store'
    path('create-store', views.create_store, name='create-store'),

    # When the URL matches 'add-product', call the 'add_product' function in the views module and name it 'add_product'
    path('add-product', views.add_product, name='add_product'),

    # When the URL matches 'store-dashboard', call the 'store_dashboard' function in the views module and name it 'store_dashboard'
    path('store-dashboard', views.store_dashboard, name='store_dashboard'),

    # When the URL matches 'store/<str:pk>', call the 'store' function in the views module and name it 'store'
    path('store/<str:pk>', views.store, name='store'),

    # When the URL matches 'product/<str:pk>', call the 'product' function in the views module and name it 'product'
    path('product/<str:pk>', views.product, name='product'),

    # When the URL matches 'search', call the 'search' function in the views module and name it 'search'
    path('search', views.search, name='search'),

    # When the URL matches 'account', call the 'account' function in the views module and name it 'account'
    path('account', views.account, name='account'),

    # When the URL matches 'create_or_update_address', call the 'create_or_update_address' function in the views module and name it 'create_or_update_address'
    path('create_or_update_address', views.create_or_update_address, name='create_or_update_address'),

    # When the URL matches 'update_profile_details', call the 'update_profile_details' function in the views module and name it 'update_profile_details'
    path('update_profile_details', views.update_profile_details, name='update_profile_details'),

    # When the URL matches 'cart', call the 'cart' function in the views module and name it 'cart'
    path('cart', views.cart, name='cart'),

    # When the URL matches 'add_to_cart', call the 'add_to_cart' function in the views module and name it 'add_to_cart'
    path('add_to_cart', views.add_to_cart, name='add_to_cart'),

    # When the URL matches 'update-cart-product', call the 'update_cart_product' function in the views module and name it 'update_cart_product'
    path('update-cart-product', views.update_cart_product, name='update_cart_product'),

    # When the URL matches 'checkout', call the 'checkout' function in the views module and name it 'checkout'
    path('checkout', views.checkout, name='checkout'),

    # When the URL matches 'payment-complete', call the 'payment_complete' function in the views module and name it 'payment-complete'
    path('payment-complete', views.payment_complete, name='payment-complete'),

    # When the URL matches 'get-cart-count', call the 'get_cart_count' function in the views module and name it 'get-cart-count'
    path('get-cart-count', views.get_cart_count, name='get-cart-count'),

    # When the URL matches 'remove-cart-product', call the 'remove_cart_product' function in the views module and name it 'remove_cart_product'
    path('remove-cart-product', views.remove_cart_product, name='remove_cart_product'),

    # When the URL matches 'invoice', call the 'invoice' function in the views module and name it 'invoice'
    path('invoice', views.invoice, name='invoice'),

    # When the URL matches 'orders', call the 'orders' function in the views module and name it 'orders'
    path('orders', views.orders, name='orders'),

    # When the URL matches 'wishlist', call the 'wishlist' function in the views module and name it 'wishlist'
    path('wishlist', views.wishlist, name='wishlist'),

    # When the URL matches 'add-to-wishlist/<str:product_id>/', call the 'AddToWishlistView' class-based view in the views module and name it 'add_to_wishlist'
    path('add-to-wishlist/<str:product_id>/', views.AddToWishlistView.as_view(), name='add_to_wishlist'),

    # When the URL matches 'remove-from-wishlist/<str:product_id>/', call the 'remove_from_wishlist' function in the views module and name it 'remove_from_wishlist'
    path('remove-from-wishlist/<str:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # When the URL matches 'store-dashboard/orders', call the 'store_dashboard_orders' function in the views module and name it 'store_dashboard_orders'
    path('store-dashboard/orders', views.store_dashboard_orders, name='store_dashboard_orders'),

    # When the URL matches 'store-dashboard/orders/<str:order_id>/', call the 'edit_order' function in the views module and name it 'edit_order'
    path('store-dashboard/orders/<str:order_id>/', views.edit_order, name='edit_order'),

    # When the URL matches 'edit-product/<str:product_id>/', call the 'edit_product' function in the views module and name it 'edit_product'
    path('edit-product/<str:product_id>/', views.edit_product, name='edit_product'),

    # When the URL matches 'delete-product/', call the 'delete_product' function in the views module and name it 'delete_product'
    path('delete-product', views.delete_product, name='delete_product'),

]