from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.PublicProductListView.as_view(), name='marketplace'),
    path('marketplace/', views.PublicProductListView.as_view(), name='marketplace'),
    path('products/<int:pk>/', views.PublicProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/review/', views.ReviewCreateView.as_view(), name='product-review'),

    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Farmer product management
    path('farmer/products/', views.ProductListView.as_view(), name='farmer-products'),
    path('farmer/products/add/', views.ProductCreateView.as_view(), name='product-add'),
    path('farmer/products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product-edit'),
    path('farmer/products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),

    # Cart + checkout
    path('cart/', views.CartDetailView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.CartAddView.as_view(), name='cart-add'),
    path('cart/remove/<int:product_id>/', views.CartRemoveView.as_view(), name='cart-remove'),
    path('cart/update/', views.CartUpdateView.as_view(), name='cart-update'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),

    # Orders
    path('buyer/orders/', views.BuyerOrderListView.as_view(), name='buyer-orders'),
    path('buyer/orders/<int:pk>/', views.BuyerOrderDetailView.as_view(), name='buyer-order-detail'),
    path('buyer/orders/<int:pk>/pay/', views.BuyerPayOrderView.as_view(), name='buyer-order-pay'),

    path('farmer/orders/', views.FarmerOrderListView.as_view(), name='farmer-orders'),
    path('farmer/orders/<int:pk>/', views.FarmerOrderDetailView.as_view(), name='farmer-order-detail'),
    path('farmer/orders/<int:pk>/status/', views.FarmerOrderStatusUpdateView.as_view(), name='farmer-order-status'),

    # Messaging system
    path('messages/', views.ConversationListView.as_view(), name='conversation-list'),
    path('messages/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('messages/<int:pk>/send/', views.MessageCreateView.as_view(), name='message-create'),
    path('products/<int:product_id>/message/', views.start_product_conversation, name='start-conversation'),
]
