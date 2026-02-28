"""
Messaging System URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ConversationListView.as_view(), name='conversation-list'),
    path('<int:pk>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('<int:pk>/send/', views.MessageCreateView.as_view(), name='message-create'),
    path('start/<int:product_id>/', views.CreateConversationView.as_view(), name='start-conversation'),
    path('product/<int:product_id>/', views.start_product_conversation, name='quick-start-conversation'),
]
