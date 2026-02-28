"""
API URL Configuration for n8n automation
"""
from django.urls import path
from . import views

urlpatterns = [
    path('send-auto-message/', views.SendAutoMessageView.as_view(), name='send-auto-message'),
    path('health/', views.HealthCheckView.as_view(), name='api-health'),
]
