from django.contrib import admin
from .models import Product, SalesRecord


# Register your models here.

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_quantity', 'unit_price', 'supplier', 'next_restock_date')
    search_fields = ('name', 'supplier', 'location')
    list_filter = ('supplier', 'location', 'next_restock_date')

@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = ("product", "date", "quantity")
    list_filter = ("product", "date")
