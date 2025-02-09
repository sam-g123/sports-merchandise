from django.contrib import admin
from .models import Product, SalesRecord, RestockHistory

class RestockHistoryInline(admin.TabularInline):
    model = RestockHistory
    extra = 1  # Allows adding new restocks from the Product admin page

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'get_sold_quantity', 'get_available_stock', 'unit_price', 'supplier', 'total_price', 'qr_code')
    search_fields = ('name', 'supplier', 'location')
    list_filter = ('supplier', 'location')

    inlines = [RestockHistoryInline]  # Restocks should be added via inline form

    readonly_fields = ('stock_quantity',)  # Make stock quantity read-only

    def get_sold_quantity(self, obj):
        return obj.get_sold_quantity()
    get_sold_quantity.short_description = "Sold Quantity"

    def get_available_stock(self, obj):
        return obj.get_available_stock()
    get_available_stock.short_description = "Available Stock"

    def save_model(self, request, obj, form, change):
        obj.generate_qr_code()
        super().save_model(request, obj, form, change)

@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = ("product", "date", "quantity")
    list_filter = ("product", "date")

@admin.register(RestockHistory)
class RestockHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'timestamp')
    ordering = ('-timestamp',)
    