from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


# ==========================
# CUSTOM USER
# ==========================

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username


# ==========================
# FARMER PROFILE
# ==========================

class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    farm_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.farm_name


# ==========================
# CATEGORY
# ==========================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name.title()


# ==========================
# PRODUCT
# ==========================

class Product(models.Model):
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_available = models.IntegerField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ==========================
# ORDER
# ==========================

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    )

    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'buyer'}
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_amount(self):
        return sum(item.subtotal() for item in self.items.all())

    def __str__(self):
        return f"Order #{self.id}"


# ==========================
# ORDER ITEM
# ==========================

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if self.quantity > self.product.quantity_available:
            raise ValidationError("Not enough stock available.")

    def save(self, *args, **kwargs):
        self.clean()

        # Set price at time of purchase
        if self.price_at_time is None:
            self.price_at_time = self.product.price

        super().save(*args, **kwargs)

    def subtotal(self):
        return self.quantity * self.price_at_time

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"


# ==========================
# PAYMENT
# ==========================

class Payment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Automatically set payment amount to order total
        self.amount = self.order.total_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment for Order #{self.order.id}"


# ==========================
# REVIEW SYSTEM
# ==========================

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'buyer'}
    )
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'buyer'], name='unique_review_per_buyer_product'),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.rating}/5"


# ==========================
# MESSAGING SYSTEM
# ==========================

class Conversation(models.Model):
    buyer = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name="buyer_conversations",
        limit_choices_to={'user_type': 'buyer'}
    )
    farmer = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name="farmer_conversations",
        limit_choices_to={'user_type': 'farmer'}
    )
    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name="conversations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("buyer", "farmer", "product")
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['buyer', '-updated_at']),
            models.Index(fields=['farmer', '-updated_at']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        product_name = f" about {self.product.name}" if self.product else ""
        return f"Conversation: {self.buyer.username} ↔ {self.farmer.username}{product_name}"

    def clean(self):
        if self.buyer == self.farmer:
            raise ValidationError("Buyer and farmer cannot be the same user.")
        
        if self.buyer.user_type != 'buyer':
            raise ValidationError("First participant must be a buyer.")
        
        if self.farmer.user_type != 'farmer':
            raise ValidationError("Second participant must be a farmer.")

    def other_participant(self, user):
        """Return the other participant in the conversation"""
        if user == self.buyer:
            return self.farmer
        elif user == self.farmer:
            return self.buyer
        return None

    @property
    def last_message(self):
        """Get the most recent message"""
        return self.messages.last()

    def unread_count(self, user):
        """Count unread messages for a specific user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name="messages"
    )
    sender = models.ForeignKey('User', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_automated = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_read']),
            models.Index(fields=['is_automated']),
        ]

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp.strftime('%H:%M')}"

    def clean(self):
        # Validate sender is part of the conversation
        if self.sender not in [self.conversation.buyer, self.conversation.farmer]:
            raise ValidationError("Sender must be a participant in the conversation.")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Update conversation timestamp
        self.conversation.save()
        
        # Trigger n8n webhook for new buyer messages
        if is_new and not self.is_automated:
            from .webhook import trigger_n8n_webhook_async
            trigger_n8n_webhook_async(self)

    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            super().save(update_fields=['is_read'])

    @property
    def is_from_buyer(self):
        """Check if message is from buyer"""
        return self.sender == self.conversation.buyer

    @property
    def is_from_farmer(self):
        """Check if message is from farmer"""
        return self.sender == self.conversation.farmer
