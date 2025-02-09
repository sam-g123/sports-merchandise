from django.shortcuts import render, get_object_or_404
from .models import Product, SalesRecord
import json
from django.db.models.functions import Lower, Trim


# Create your views here.

def product_list(request):
    selected_category = request.GET.get('category')  # Get category from URL query param
    products = Product.objects.all()
    if selected_category:
        products = products.filter(category__iexact=selected_category)  # Case-insensitive filter
    categories = (
        Product.objects.exclude(category__isnull=True)
        .exclude(category__exact="")
        .annotate(clean_category=Trim(Lower('category')))
        .values_list('clean_category', flat=True)
        .distinct()
    )
    return render(request, 'products/product_list.html', {'products': products, 'categories': categories, 'selected_category': selected_category})

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

