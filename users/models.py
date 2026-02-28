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
