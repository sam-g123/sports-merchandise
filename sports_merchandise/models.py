from django.db import models

# Create your models here.

class Product(models.Model):
    image = models.ImageField(null=True, blank=True)
    name = models.CharField(max_length=255)
    stock_quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    description = models.TextField()
    supplier = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    previous_restock_date = models.DateField(null=True, blank=True)
    next_restock_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.stock_quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class SalesRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales_records")
    date = models.DateField()
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} units of {self.product.name} on {self.date}"
