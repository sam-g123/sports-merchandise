from django.shortcuts import render, get_object_or_404
from .models import Product, SalesRecord
import json


# Create your views here.

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Get sales data for the product
    sales = SalesRecord.objects.filter(product=product).order_by("date")
    sales_data = {
        "labels": [sale.date.strftime("%Y-%m-%d") for sale in sales],
        "sales": [sale.quantity for sale in sales],
    }

    return render(request, "products/product_detail.html", {
        "product": product,
        "sales_data": json.dumps(sales_data),
    })

