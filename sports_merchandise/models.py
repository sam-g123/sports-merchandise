import qrcode
from django.core.files.base import ContentFile
from io import BytesIO
from django.urls import reverse
from django.db import models
from django.db.models import Sum
from django.utils import timezone

# Create your models here.

class Product(models.Model):
    image = models.ImageField(null=True, blank=True)
    name = models.CharField(max_length=255)
    stock_quantity = models.PositiveIntegerField() # Original stock before sales
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    description = models.TextField()
    supplier = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    previous_restock_date = models.DateField(null=True, blank=True, editable=False)  # Timestamped previous restock date
    restock_quantity = models.PositiveIntegerField(null=True, blank=True)  # Restock quantity to add to stock
    restock_date = models.DateTimeField(null=True, blank=True)  # Timestamped restock date
    qr_code = models.ImageField(blank=True, null=True)
    # add categories


    def get_absolute_url(self):
        return reverse('product_detail', args=[str(self.id)])

    def generate_qr_code(self):
        """Generate and save a QR code linking to the product's details page."""
        url = f"http://10.42.0.1:9000{self.get_absolute_url()}"
        qr = qrcode.make(url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        self.qr_code.save(f"{self.name}_qr.png", ContentFile(buffer.getvalue()), save=False)

    def get_sold_quantity(self):
        from .models import SalesRecord  # Import here to avoid circular import issues
        sales = SalesRecord.objects.filter(product=self).aggregate(total_sold=Sum('quantity'))['total_sold']
        return sales if sales else 0

    def get_available_stock(self):
        return self.stock_quantity - self.get_sold_quantity()
    
    def add_restock(self, quantity, restock_date=None):
        """
        Update stock with the given quantity, timestamp it, and log it in RestockHistory.
        """
        if quantity > 0:
            restock_date = restock_date or timezone.now()
            
            # Create a new entry in RestockHistory
            RestockHistory.objects.create(product=self, quantity=quantity, timestamp=restock_date)

            # Update stock quantity
            self.stock_quantity += quantity
            self.previous_restock_date = self.restock_date
            self.restock_date = restock_date
            self.save()
    
    def save(self, *args, **kwargs):
        self.generate_qr_code()  # Auto-generate QR code before saving
        self.total_price = self.get_available_stock()  * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Available: {self.get_available_stock()})"

class SalesRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales_records")
    date = models.DateField()
    quantity = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if self.pk is None:  # Only reduce stock on new sales, not updates
            self.product.stock_quantity -= self.quantity  # Reduce stock quantity
            self.product.save()  # Save the updated stock quantity

        super().save(*args, **kwargs)  # Save the SalesRecord


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

