from django.contrib import admin
from .models import User, FarmerProfile, Category, Product, Order

admin.site.register(User)
admin.site.register(FarmerProfile)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
