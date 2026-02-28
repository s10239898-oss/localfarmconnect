from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Prefetch
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from django.urls import reverse_lazy

from .forms import CustomUserCreationForm, ProductForm, ReviewForm
from .models import Category, FarmerProfile, Order, OrderItem, Payment, Product, Review, Conversation, Message


# =====================================================
# REGISTRATION
# =====================================================

@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Automatically create FarmerProfile if user is farmer
            if user.user_type == 'farmer':
                FarmerProfile.objects.create(
                    user=user,
                    farm_name=f"{user.username}'s Farm",
                    location="Not Set"
                )

            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


# =====================================================
# DASHBOARD
# =====================================================

@login_required
def dashboard(request):
    if request.user.user_type == 'farmer':
        return render(request, 'users/farmer_dashboard.html')
    else:
        return render(request, 'users/buyer_dashboard.html')


# =====================================================
# SECURITY MIXIN (FARMERS ONLY)
# =====================================================

class FarmerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.user_type == 'farmer'

class BuyerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.user_type == 'buyer'


# =====================================================
# PRODUCT CREATE
# =====================================================

class ProductCreateView(FarmerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'users/product_form.html'
    success_url = reverse_lazy('farmer-products')

    def form_valid(self, form):
        farmer_profile = FarmerProfile.objects.get(user=self.request.user)
        form.instance.farmer = farmer_profile
        return super().form_valid(form)


# =====================================================
# PRODUCT LIST (FARMER ONLY)
# =====================================================

class ProductListView(FarmerRequiredMixin, ListView):
    model = Product
    template_name = 'users/farmer_products.html'
    context_object_name = 'products'

    def get_queryset(self):
        farmer_profile = FarmerProfile.objects.get(user=self.request.user)
        return Product.objects.filter(farmer=farmer_profile)


# =====================================================
# PRODUCT UPDATE
# =====================================================

class ProductUpdateView(FarmerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'users/product_form.html'
    success_url = reverse_lazy('farmer-products')

    def get_queryset(self):
        farmer_profile = FarmerProfile.objects.get(user=self.request.user)
        return Product.objects.filter(farmer=farmer_profile)


# =====================================================
# PRODUCT DELETE
# =====================================================

class ProductDeleteView(FarmerRequiredMixin, DeleteView):
    model = Product
    template_name = 'users/product_confirm_delete.html'
    success_url = reverse_lazy('farmer-products')

    def get_queryset(self):
        farmer_profile = FarmerProfile.objects.get(user=self.request.user)
        return Product.objects.filter(farmer=farmer_profile)


# =====================================================
# PHASE 4 — PUBLIC MARKETPLACE (BUYER SIDE)
# =====================================================

class PublicProductListView(ListView):
    model = Product
    template_name = 'users/marketplace_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Product.objects.filter(quantity_available__gt=0)
            .select_related('category', 'farmer', 'farmer__user')
            .order_by('-created_at')
        )
        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.order_by('name')
        ctx['selected_category'] = self.request.GET.get('category', '')
        return ctx


class PublicProductDetailView(DetailView):
    model = Product
    template_name = 'users/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.select_related('category', 'farmer', 'farmer__user').prefetch_related('reviews')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = ctx['product']
        ctx['avg_rating'] = product.reviews.aggregate(avg=Avg('rating'))['avg']
        ctx['review_count'] = product.reviews.count()

        can_review = False
        has_reviewed = False
        if self.request.user.is_authenticated and getattr(self.request.user, 'user_type', None) == 'buyer':
            has_reviewed = Review.objects.filter(product=product, buyer=self.request.user).exists()
            purchased_delivered = OrderItem.objects.filter(
                order__buyer=self.request.user,
                order__status='delivered',
                product=product,
            ).exists()
            can_review = purchased_delivered and not has_reviewed

        ctx['can_review'] = can_review
        ctx['has_reviewed'] = has_reviewed
        return ctx


# =====================================================
# PHASE 5 — SESSION CART
# =====================================================

SESSION_CART_KEY = 'cart'


def _get_cart(session):
    cart = session.get(SESSION_CART_KEY)
    if not isinstance(cart, dict):
        cart = {}
        session[SESSION_CART_KEY] = cart
    return cart


def _save_cart(session, cart):
    session[SESSION_CART_KEY] = cart
    session.modified = True


class CartDetailView(BuyerRequiredMixin, TemplateView):
    template_name = 'users/cart_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cart = _get_cart(self.request.session)
        product_ids = [int(pid) for pid in cart.keys()]

        products = (
            Product.objects.filter(id__in=product_ids)
            .select_related('category', 'farmer', 'farmer__user')
        )
        products_by_id = {p.id: p for p in products}

        items = []
        total = Decimal('0.00')
        for pid_str, entry in cart.items():
            pid = int(pid_str)
            product = products_by_id.get(pid)
            if not product:
                continue
            qty = int(entry.get('quantity', 0))
            qty = max(qty, 0)
            line_total = (product.price * qty) if qty else Decimal('0.00')
            total += line_total
            items.append({
                'product': product,
                'quantity': qty,
                'line_total': line_total,
                'max_qty': max(product.quantity_available, 0),
            })

        ctx['items'] = items
        ctx['total'] = total
        return ctx


class CartAddView(BuyerRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        if product.quantity_available <= 0:
            messages.error(request, "This product is out of stock.")
            return redirect('product-detail', pk=product.id)

        try:
            qty = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            qty = 1
        qty = max(qty, 1)

        cart = _get_cart(request.session)
        current_qty = int(cart.get(str(product.id), {}).get('quantity', 0))
        new_qty = current_qty + qty

        if new_qty > product.quantity_available:
            new_qty = product.quantity_available
            messages.warning(request, "Quantity adjusted to available stock.")
        cart[str(product.id)] = {'quantity': new_qty}
        _save_cart(request.session, cart)
        messages.success(request, "Added to cart.")
        return redirect('cart')


class CartRemoveView(BuyerRequiredMixin, View):
    def post(self, request, product_id):
        cart = _get_cart(request.session)
        cart.pop(str(product_id), None)
        _save_cart(request.session, cart)
        messages.success(request, "Removed from cart.")
        return redirect('cart')


class CartUpdateView(BuyerRequiredMixin, View):
    def post(self, request):
        cart = _get_cart(request.session)
        remove_pid = request.POST.get('remove')
        if remove_pid:
            cart.pop(str(remove_pid), None)
            _save_cart(request.session, cart)
            messages.success(request, "Removed from cart.")
            return redirect('cart')

        product_ids = [int(pid) for pid in cart.keys()]
        products = Product.objects.filter(id__in=product_ids)
        products_by_id = {p.id: p for p in products}

        updated = {}
        for pid_str in cart.keys():
            product = products_by_id.get(int(pid_str))
            if not product:
                continue
            raw = request.POST.get(f'qty_{pid_str}', None)
            try:
                qty = int(raw)
            except (TypeError, ValueError):
                qty = int(cart.get(pid_str, {}).get('quantity', 0))

            if qty <= 0:
                continue
            qty = min(qty, max(product.quantity_available, 0))
            updated[pid_str] = {'quantity': qty}

        _save_cart(request.session, updated)
        messages.success(request, "Cart updated.")
        return redirect('cart')


# =====================================================
# PHASE 6 — CHECKOUT & ORDER CREATION (MULTI-VENDOR)
# =====================================================

class CheckoutView(BuyerRequiredMixin, TemplateView):
    template_name = 'users/checkout.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cart = _get_cart(self.request.session)
        if not cart:
            ctx['items'] = []
            ctx['total'] = Decimal('0.00')
            return ctx

        product_ids = [int(pid) for pid in cart.keys()]
        products = (
            Product.objects.filter(id__in=product_ids)
            .select_related('farmer', 'farmer__user', 'category')
        )
        products_by_id = {p.id: p for p in products}

        items = []
        total = Decimal('0.00')
        for pid_str, entry in cart.items():
            product = products_by_id.get(int(pid_str))
            if not product:
                continue
            qty = int(entry.get('quantity', 0))
            qty = max(qty, 0)
            line_total = product.price * qty if qty else Decimal('0.00')
            total += line_total
            items.append({'product': product, 'quantity': qty, 'line_total': line_total})

        ctx['items'] = items
        ctx['total'] = total
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        cart = _get_cart(request.session)
        if not cart:
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        product_ids = [int(pid) for pid in cart.keys()]
        products = (
            Product.objects.select_for_update()
            .filter(id__in=product_ids)
            .select_related('farmer')
        )
        products_by_id = {p.id: p for p in products}

        # Validate stock under lock
        for pid_str, entry in cart.items():
            product = products_by_id.get(int(pid_str))
            if not product:
                raise Http404("Product not found.")
            qty = int(entry.get('quantity', 0))
            if qty <= 0:
                messages.error(request, "Invalid cart quantity.")
                return redirect('cart')
            if qty > product.quantity_available:
                messages.error(request, f"Not enough stock for {product.name}.")
                return redirect('cart')

        # Group items by farmer to create one Order per farmer (multi-vendor)
        grouped = {}
        for pid_str, entry in cart.items():
            product = products_by_id[int(pid_str)]
            qty = int(entry.get('quantity', 0))
            grouped.setdefault(product.farmer_id, []).append((product, qty))

        created_orders = []
        for farmer_id, entries in grouped.items():
            order = Order.objects.create(buyer=request.user, status='pending')
            for product, qty in entries:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price_at_time=product.price,
                )
                product.quantity_available -= qty
                product.save(update_fields=['quantity_available'])

            Payment.objects.create(order=order, status='pending', amount=order.total_amount)
            created_orders.append(order.id)

        # Clear cart + remember order ids for a success message
        request.session[SESSION_CART_KEY] = {}
        request.session['last_order_ids'] = created_orders
        request.session.modified = True

        messages.success(request, f"Checkout complete. Created {len(created_orders)} order(s).")
        return redirect('buyer-orders')


# =====================================================
# PHASE 7 — ORDER LIFECYCLE
# =====================================================

class BuyerOrderListView(BuyerRequiredMixin, ListView):
    model = Order
    template_name = 'users/buyer_orders.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        return (
            Order.objects.filter(buyer=self.request.user)
            .select_related('buyer')
            .prefetch_related('items__product')
            .order_by('-created_at')
        )


class BuyerOrderDetailView(BuyerRequiredMixin, DetailView):
    model = Order
    template_name = 'users/buyer_order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return (
            Order.objects.filter(buyer=self.request.user)
            .select_related('buyer')
            .prefetch_related('items__product', 'items__product__farmer', 'items__product__farmer__user')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['payment'] = Payment.objects.filter(order=self.object).first()
        return ctx


class BuyerPayOrderView(BuyerRequiredMixin, View):
    @transaction.atomic
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, buyer=request.user)
        payment = getattr(order, 'payment', None)
        if not payment:
            raise Http404("Payment not found.")
        payment.status = 'completed'
        payment.save()
        if order.status in {'pending', 'confirmed'}:
            order.status = 'paid'
            order.save(update_fields=['status'])
        messages.success(request, "Payment marked as completed (MVP simulation).")
        return redirect('buyer-order-detail', pk=order.id)


class FarmerOrderListView(FarmerRequiredMixin, ListView):
    model = Order
    template_name = 'users/farmer_orders.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        farmer_profile = FarmerProfile.objects.get(user=self.request.user)
        item_qs = OrderItem.objects.select_related('product').filter(product__farmer=farmer_profile)
        return (
            Order.objects.filter(items__product__farmer=farmer_profile)
            .distinct()
            .prefetch_related(Prefetch('items', queryset=item_qs))
            .order_by('-created_at')
        )


class FarmerOrderDetailView(FarmerRequiredMixin, DetailView):
    model = Order
    template_name = 'users/farmer_order_detail.html'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        farmer_profile = FarmerProfile.objects.get(user=self.request.user)
        order = get_object_or_404(
            Order.objects.filter(items__product__farmer=farmer_profile).distinct(),
            pk=self.kwargs['pk'],
        )
        return order

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        farmer_profile = FarmerProfile.objects.get(user=self.request.user)
        ctx['order_items'] = (
            self.object.items.select_related('product')
            .filter(product__farmer=farmer_profile)
        )
        return ctx


class FarmerOrderStatusUpdateView(FarmerRequiredMixin, View):
    allowed_statuses = {'confirmed', 'shipped', 'delivered'}

    @transaction.atomic
    def post(self, request, pk):
        farmer_profile = FarmerProfile.objects.get(user=request.user)
        order = get_object_or_404(
            Order.objects.filter(items__product__farmer=farmer_profile).distinct(),
            pk=pk,
        )
        new_status = request.POST.get('status')
        if new_status not in self.allowed_statuses:
            messages.error(request, "Invalid status.")
            return redirect('farmer-order-detail', pk=order.id)
        order.status = new_status
        order.save(update_fields=['status'])
        messages.success(request, "Order status updated.")
        return redirect('farmer-order-detail', pk=order.id)


# =====================================================
# PHASE 8 — REVIEWS
# =====================================================

class ReviewCreateView(BuyerRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'users/review_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs['pk'])
        # Must have a delivered purchase of this product
        purchased_delivered = OrderItem.objects.filter(
            order__buyer=request.user,
            order__status='delivered',
            product=self.product,
        ).exists()
        if not purchased_delivered:
            raise Http404("You can only review products from delivered orders.")
        # Prevent duplicates
        if Review.objects.filter(product=self.product, buyer=request.user).exists():
            messages.info(request, "You have already reviewed this product.")
            return redirect('product-detail', pk=self.product.id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.product = self.product
        form.instance.buyer = self.request.user
        messages.success(self.request, "Review submitted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('product-detail', kwargs={'pk': self.product.id})


# =====================================================
# MESSAGING SYSTEM
# =====================================================

# -----------------------
# SECURITY MIXINS
# -----------------------

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


# -----------------------
# CONVERSATION LIST VIEW
# -----------------------

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


# -----------------------
# CONVERSATION DETAIL VIEW
# -----------------------

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


# -----------------------
# CREATE CONVERSATION VIEW
# -----------------------

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


# -----------------------
# MESSAGE CREATE VIEW
# -----------------------

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


# -----------------------
# QUICK MESSAGE FROM PRODUCT
# -----------------------

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
