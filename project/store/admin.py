from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'volume', 'in_stock', 'created_at')
    list_filter = ('category', 'in_stock')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'in_stock')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_at', 'updated_at')
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'first_name', 'last_name', 'phone',
        'status', 'payment_method', 'payment_status',
        'total_price', 'created_at',
    )
    list_filter = ('status', 'payment_method', 'payment_status')
    search_fields = ('first_name', 'last_name', 'phone', 'transaction_id')
    list_editable = ('status', 'payment_status')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Клиент', {
            'fields': ('user', 'first_name', 'last_name', 'phone', 'address'),
        }),
        ('Заказ', {
            'fields': ('status', 'total_price', 'comment',
                       'created_at', 'updated_at'),
        }),
        ('Оплата', {
            'fields': ('payment_method', 'payment_status', 'transaction_id'),
        }),
    )
    inlines = [OrderItemInline]
