from django.contrib import admin
from .models import User, FarmerProfile, Category, Product, Order, Conversation, Message

admin.site.register(User)
admin.site.register(FarmerProfile)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)

# Messaging system admin
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'farmer', 'product', 'created_at', 'updated_at']
    list_filter = ['created_at', 'product']
    search_fields = ['buyer__username', 'farmer__username', 'product__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'buyer', 'farmer', 'product'
        )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_preview', 'timestamp', 'is_read']
    list_filter = ['timestamp', 'is_read']
    search_fields = ['sender__username', 'content']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conversation', 'sender', 'conversation__buyer', 'conversation__farmer'
        )
