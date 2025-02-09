import qrcode
from django.core.files.base import ContentFile
from io import BytesIO
from django.urls import reverse
from django.db import models
from django.db.models import Sum
from django.utils import timezone
import os
from django.conf import settings

class Product(models.Model):
    image = models.ImageField(null=True, blank=True)
    name = models.CharField(max_length=255)
    stock_quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.00)
    description = models.TextField()
    category = models.CharField(max_length=100)
    supplier = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    previous_restock_date = models.DateField(null=True, blank=True, editable=False)
    restock_date = models.DateTimeField(null=True, blank=True)
    qr_code = models.ImageField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse('product_detail', args=[str(self.id)])

    def generate_qr_code(self):
        """Generate QR code only if the product has an ID."""
        if not self.pk:
            return  # Ensure the object is saved before generating the QR code

        # Fetch the base URL from .env, defaulting to localhost if not set
        base_url = getattr(settings, "QR_CODE_BASE_URL", "http://localhost:8000")
        url = f"{base_url}{self.get_absolute_url()}"
        qr = qrcode.make(url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        self.qr_code.save(f"{self.name}_qr.png", ContentFile(buffer.getvalue()), save=False)

    def get_sold_quantity(self):
        if not self.pk:
            return 0
        sales = self.sales_records.aggregate(total_sold=Sum('quantity'))['total_sold']
        return sales if sales else 0

    def get_available_stock(self):
        """Calculate stock based on total restocks minus sales."""
        if not self.pk:
            return 0  # If the product is not saved yet, available stock is 0

        # Get total restocked quantity (sum of all restocks)
        total_restocked = self.restockhistory_set.aggregate(total=Sum('quantity'))['total'] or 0

        # Get total sold quantity
        total_sold = self.sales_records.aggregate(total=Sum('quantity'))['total'] or 0

        # Available stock = Total restocked - Total sold
        return max(0, total_restocked - total_sold)

    def add_restock(self, quantity, restock_date=None):
        if quantity > 0:
            restock_date = restock_date or timezone.now()
            restock_history = RestockHistory.objects.filter(product=self)

            if not restock_history.exists():
                self.stock_quantity = quantity  # First restock sets the stock
            else:
                self.stock_quantity += quantity  # Normal restock adds to stock

            self.previous_restock_date = self.restock_date
            self.restock_date = restock_date
            self.save()

            RestockHistory.objects.create(product=self, quantity=quantity, timestamp=restock_date)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Save initially to get an ID

        # Generate QR code only after saving the product with a valid ID
        if is_new and not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])  # Save QR code only

        self.total_price = self.get_available_stock() * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Available: {self.get_available_stock()})"

class SalesRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales_records")
    date = models.DateField()
    quantity = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if self.pk is None:  # Only reduce stock on new sales, not updates
            self.product.stock_quantity -= self.quantity
            self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} sold on {self.date}"

class RestockHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='restockhistory_set')
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} - Restocked {self.quantity} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    class Meta:
        verbose_name_plural = "Restock Histories"
