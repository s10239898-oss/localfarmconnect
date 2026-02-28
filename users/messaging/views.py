"""
Messaging System Views
Class-based views for managing conversations and messages.
"""
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from django.http import Http404
from django.contrib import messages

from users.models import Conversation, Message, Product, FarmerProfile


logger = logging.getLogger(__name__)


# ==========================
# SECURITY MIXINS
# ==========================

class ConversationAccessMixin(LoginRequiredMixin):
    """Mixin to ensure user can access conversation"""
    
    def get_conversation(self):
        if not hasattr(self, 'conversation'):
            pk = self.kwargs.get('pk')
            self.conversation = get_object_or_404(Conversation, pk=pk)
            
            # Security check: user must be participant
            if self.request.user not in [self.conversation.buyer, self.conversation.farmer]:
                raise PermissionDenied("You don't have access to this conversation.")
        
        return self.conversation


class BuyerRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is a buyer"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != 'buyer':
            raise PermissionDenied("This feature is only available to buyers.")
        return super().dispatch(request, *args, **kwargs)


class FarmerRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is a farmer"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != 'farmer':
            raise PermissionDenied("This feature is only available to farmers.")
        return super().dispatch(request, *args, **kwargs)


# ==========================
# CONVERSATION LIST VIEW
# ==========================

class ConversationListView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'messages/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'buyer':
            return Conversation.objects.filter(buyer=user).select_related(
                'farmer', 'product', 'product__farmer', 'product__category'
            ).prefetch_related('messages')
        elif user.user_type == 'farmer':
            return Conversation.objects.filter(farmer=user).select_related(
                'buyer', 'product', 'product__farmer', 'product__category'
            ).prefetch_related('messages')
        else:
            return Conversation.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add unread counts
        conversations = context['conversations']
        for conv in conversations:
            conv.unread_messages = conv.unread_count(self.request.user)
        
        return context


# ==========================
# CONVERSATION DETAIL VIEW
# ==========================

class ConversationDetailView(ConversationAccessMixin, DetailView):
    model = Conversation
    template_name = 'messages/conversation_detail.html'
    context_object_name = 'conversation'

    def get_object(self):
        return self.get_conversation()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context['conversation']
        
        # Mark unread messages as read
        unread_messages = conversation.messages.filter(
            is_read=False
        ).exclude(sender=self.request.user)
        
        for message in unread_messages:
            message.mark_as_read()
        
        # Get messages for display
        context['messages'] = conversation.messages.all().select_related('sender')
        
        # Determine if current user is buyer or farmer
        context['is_buyer'] = self.request.user == conversation.buyer
        context['is_farmer'] = self.request.user == conversation.farmer
        context['other_user'] = conversation.other_participant(self.request.user)
        
        return context


# ==========================
# CREATE CONVERSATION VIEW
# ==========================

class CreateConversationView(BuyerRequiredMixin, CreateView):
    model = Conversation
    template_name = 'messages/create_conversation.html'
    fields = []  # We'll handle form processing manually

    def dispatch(self, request, *args, **kwargs):
        # Get product first
        self.product = get_object_or_404(Product, pk=self.kwargs['product_id'])
        
        # Get farmer from product
        self.farmer = self.product.farmer.user
        
        # Security: buyer cannot message themselves
        if request.user == self.farmer:
            raise PermissionDenied("You cannot message yourself.")
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        context['farmer'] = self.farmer
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        message_content = request.POST.get('message', '').strip()
        
        if not message_content:
            messages.error(request, "Please enter a message.")
            return self.get(request, *args, **kwargs)
        
        # Check if conversation already exists
        conversation, created = Conversation.objects.get_or_create(
            buyer=request.user,
            farmer=self.farmer,
            product=self.product
        )
        
        # Create initial message
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )
        
        if created:
            messages.success(request, "Conversation started successfully!")
        else:
            messages.info(request, "Message added to existing conversation.")
        
        return redirect('conversation-detail', pk=conversation.pk)


# ==========================
# MESSAGE CREATE VIEW
# ==========================

class MessageCreateView(ConversationAccessMixin, View):
    """Handle message creation via POST"""
    
    def post(self, request, pk):
        conversation = self.get_conversation()
        message_content = request.POST.get('message', '').strip()
        
        if not message_content:
            messages.error(request, "Please enter a message.")
            return redirect('conversation-detail', pk=conversation.pk)
        
        # Create message
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )
        
        messages.success(request, "Message sent!")
        return redirect('conversation-detail', pk=conversation.pk)


# ==========================
# QUICK MESSAGE FROM PRODUCT
# ==========================

@login_required
def start_product_conversation(request, product_id):
    """Quick start conversation from product detail page"""
    product = get_object_or_404(Product, pk=product_id)
    
    # Validate user is buyer
    if request.user.user_type != 'buyer':
        raise PermissionDenied("Only buyers can start conversations.")
    
    # Get farmer
    farmer = product.farmer.user
    
    # Check if trying to message self
    if request.user == farmer:
        raise PermissionDenied("You cannot message yourself.")
    
    # Get or create conversation
    conversation, created = Conversation.objects.get_or_create(
        buyer=request.user,
        farmer=farmer,
        product=product
    )
    
    if created:
        messages.info(request, f"Conversation started with {farmer.username}. Send your first message!")
    else:
        messages.info(request, f"Existing conversation found with {farmer.username}.")
    
    return redirect('conversation-detail', pk=conversation.pk)
