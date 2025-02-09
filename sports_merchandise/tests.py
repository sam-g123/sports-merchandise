from django.test import TestCase
import unittest
from .models import Product, SalesRecord
import factory
from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile

# Factory for generating test products
class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    stock_quantity = factory.Faker('random_int', min=0, max=100)
    unit_price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    total_price = factory.LazyAttribute(lambda obj: obj.unit_price * obj.stock_quantity)  # Required, but calculated
    description = factory.Faker("text", max_nb_chars=200)
    supplier = factory.Faker("company")
    location = factory.Faker("address")
    category = factory.Faker("word")

    @factory.lazy_attribute
    def image(self):
        """Generate an in-memory test image."""
        img = ContentFile(b"fake_image_data", name="test_image.jpg")
        return img

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Ensure the instance is saved before accessing its ID."""
        obj = model_class(*args, **kwargs)
        super(model_class, obj).save()  # Save to get an ID
        obj.save()
        return obj

    @factory.post_generation
    def ensure_qr_code(self, create, extracted, **kwargs):
        if create:
            self.save()  # Save again to trigger QR code generation


# Factory for generating test sales records
class SalesRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SalesRecord

    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker("random_int", min=1, max=10)
    date = factory.LazyFunction(timezone.now)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Ensure stock is updated when a sale is recorded."""
        obj = model_class(*args, **kwargs)
        obj.save()
        return obj

class ProductModelTest(TestCase):
    def test_stock_decreases_on_sale(self):
        product = ProductFactory()
        initial_stock = product.stock_quantity
        print(f"Initial stock: {initial_stock}")  # Debugging print
        sale = SalesRecordFactory(product=product, quantity=5)
        sale.save()
        print(f"Sale created: {sale}")  # Debugging print
        
        # Refresh product from DB to get the updated stock
        product.refresh_from_db()
        print(f"Stock after sale: {product.stock_quantity}")  # Debugging print
        
        self.assertEqual(product.stock_quantity, initial_stock - 5)

    def test_stock_increases_on_restock(self):
        product = ProductFactory()
        initial_stock = product.stock_quantity

        # Simulating restock
        product.stock_quantity += 20
        product.save()

        # Refresh from DB to ensure the change is persisted
        product.refresh_from_db()
        
        self.assertEqual(product.stock_quantity, initial_stock + 20)

class ProductViewsTest(TestCase):
    def setUp(self):
        self.product = ProductFactory()

    def test_product_detail_view(self):
        url = reverse("product_detail", args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

if __name__ == "__main__":
    unittest.main()
