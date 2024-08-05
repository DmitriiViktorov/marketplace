import os
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from django.test import TestCase

from .models import (
    Product, Category, ProductImage,
    Tag, ProductTag, Review,
    Specification, Order, OrderItem,
    OrderDeliveryType, Payment, Sale
)

from myauth.models import Profile


class ProductModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(title="Electronics")
        cls.product = Product.objects.create(
            title="TV",
            count=14,
            price=199.99,
            description="Good TV",
            fullDescription="Real good one.",
            freeDelivery=True,
            category=cls.category,
            sort_index=1,
            limited_edition=True,
            banner=True
        )

    def test_product_creation(self):
        """Test that a Product instance is created correctly"""
        product = Product.objects.get(title="TV")
        self.assertEqual(product.title, "TV")
        self.assertEqual(product.count, 14)
        self.assertEqual(product.price, Decimal("199.99"))
        self.assertEqual(product.description, "Good TV")
        self.assertEqual(product.fullDescription, "Real good one.")
        self.assertTrue(product.freeDelivery)
        self.assertEqual(product.category.title, "Electronics")
        self.assertEqual(product.sort_index, 1)
        self.assertTrue(product.limited_edition)
        self.assertTrue(product.banner)

    def test_product_string_representation(self):
        """Test the string representation of the Product instance"""
        product = Product.objects.get(title="TV")
        self.assertEqual(str(product), product.title)

    def test_product_ordering(self):
        """Test that Products are ordered by title"""
        product2 = Product.objects.create(
            title="Laptop",
            count=5,
            price=999.99,
            category=self.category
        )
        products = Product.objects.all()
        self.assertEqual(products[0], product2)
        self.assertEqual(products[1], self.product)

    def test_product_count_negative(self):
        """Test that Product count cannot be negative"""
        with self.assertRaises(ValidationError):
            product = Product(
                title="Negative Count Product",
                count=-1,
                price=100.00
            )
            product.full_clean()
            product.save()

    def test_product_title_max_length(self):
        """Test that Product title cannot exceed max length"""
        with self.assertRaises(ValidationError):
            product = Product(
                title="A" * 101,
                count=5,
                price=50.00
            )
            product.full_clean()

    def test_product_price_negative(self):
        """Test that Product price cannot be negative"""
        with self.assertRaises(ValidationError):
            product = Product(
                title="Negative Price Product",
                count=10,
                price=-1.00
            )
            product.full_clean()


class ProductImageModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="TV",
            count=14,
            price=199.99,
        )
        cls.image_path = 'shopapp/test_images/default_image.png'
        with open(cls.image_path, 'rb') as image_file:
            cls.uploaded_image = SimpleUploadedFile(
                name='default_image.png',
                content=image_file.read(),
                content_type='image/png'
            )

    def test_image_creation(self):
        product_image = ProductImage.objects.create(product=self.product)
        product_image.src = self.image_path
        product_image.save()
        self.assertEqual(product_image.product, self.product)
        self.assertEqual(product_image.src, self.image_path)
        self.assertEqual(product_image.alt, self.uploaded_image.name.split('.')[0])

    def test_image_creation_new_name(self):
        product_image = ProductImage.objects.create(product=self.product)
        product_image.src = self.image_path
        product_image.alt = "test_image_name"
        product_image.save()
        self.assertEqual(product_image.alt, "test_image_name")


class CategoryModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(title="Electronics")
        cls.image_path = 'shopapp/test_images/default_image.png'
        with open(cls.image_path, 'rb') as image_file:
            cls.uploaded_image = SimpleUploadedFile(
                name='default_image.png',
                content=image_file.read(),
                content_type='image/png'
            )

    def test_category_creation(self):
        """Test that a Category instance is created correctly"""
        category = Category.objects.get(title="Electronics")
        self.assertEqual(category.title, "Electronics")
        self.assertIsNone(category.parent)

    def test_category_image_upload(self):
        """Test uploading an image to a Category"""
        category_with_image = Category.objects.create(
            title="Books"
        )
        category_with_image.src = self.uploaded_image
        category_with_image.save()
        self.assertTrue(category_with_image.src)
        self.assertEqual(category_with_image.alt, 'default_image')

    def test_category_string_representation(self):
        """Test the string representation of the Category instance"""
        category = Category.objects.get(title="Electronics")
        self.assertEqual(str(category), category.title)

    def test_category_ordering(self):
        """Test that Categories are ordered by title"""
        category2 = Category.objects.create(title="Books")
        categories = Category.objects.all()
        self.assertEqual(categories[0], category2)
        self.assertEqual(categories[1], self.category)

    def test_category_parent_relationship(self):
        child_category = Category.objects.create(
            title="Phone",
            parent=self.category
        )
        self.assertEqual(child_category.parent, self.category)
        child_categories = self.category.subcategories.all()
        self.assertIn(child_category, child_categories)

    def tearDown(self):
        for category_image in Category.objects.all():
            if category_image.src:
                if os.path.isfile(category_image.src.path):
                    os.remove(category_image.src.path)


class TagModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="TV",
            count=14,
            price=199.99,
        )

    def test_tag_creation(self):
        tag = Tag.objects.create(name="Best price")
        another_tag = Tag.objects.create(name="Sale")
        ProductTag.objects.create(product=self.product, tag=tag)
        self.assertTrue(Tag.objects.filter(name="Best price").exists())
        self.assertTrue(ProductTag.objects.filter(product=self.product, tag=tag).exists())
        product_tags = ProductTag.objects.filter(product=self.product).values_list('tag__name', flat=True)
        self.assertIn("Best price", product_tags)
        self.assertNotIn("Sale", product_tags)


class ReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="TV",
            count=14,
            price=199.99,
        )

    def test_review_creation(self):
        review = Review.objects.create(
            product=self.product,
            author="Test User",
            email="test_email@gmail.com",
            text="Test text",
            rate=5,
        )
        self.assertEqual(review.author, "Test User")
        self.assertEqual(review.email, "test_email@gmail.com")
        self.assertEqual(review.text, "Test text")
        self.assertEqual(review.rate, 5)
        self.assertEqual(review.product, self.product)

    def test_review_wrong_rate(self):
        with self.assertRaises(IntegrityError):
            review = Review.objects.create(
                product=self.product,
                author="Test User",
                email="test_email@gmail.com",
                text="Test text",
                rate=-5,
            )

    def test_review_ordering(self):
        review = Review.objects.create(
            product=self.product,
            author="First User",
            email="test_email@gmail.com",
            text="Test text",
            rate=1,
        )
        another_review = Review.objects.create(
            product=self.product,
            author="Second User",
            email="test_email2@gmail.com",
            text="Test text2",
            rate=2,
        )
        reviews = Review.objects.all()
        self.assertEqual(reviews.count(), 2)
        self.assertEqual(reviews[0].author, "Second User")
        self.assertEqual(reviews[1].author, "First User")


class SpecificationModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="TV",
            count=14,
            price=199.99,
        )

    def test_specification_creation(self):
        specification = Specification.objects.create(
            product=self.product,
            name="Test name",
            value="Test value",
        )
        self.assertEqual(specification.name, "Test name")
        self.assertEqual(specification.value, "Test value")
        self.assertEqual(specification.product, self.product)
        self.assertIn(specification, Specification.objects.all())

    def test_specification_cascade_delete(self):
        specification = Specification.objects.create(
            product=self.product,
            name="Test name",
            value="Test value",
        )
        self.product.delete()
        self.assertFalse(Specification.objects.filter(name="Test name").exists())


class OrderModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="TV",
            count=14,
            price=199.99,
        )
        cls.user = User.objects.create(
            username="Test user",
            password="password123"
        )
        cls.profile = Profile.objects.create(
            user=cls.user,
            fullName="Test User fullName"
        )

    def test_order_creation(self):
        order = Order.objects.create(
            profile=self.profile,
            deliveryType="free",
            paymentType="online",
            totalCost=199.99,
            status='accepted',
            city="London",
            address="221b, Baker str.",
        )
        self.assertEqual(order.deliveryType, "free")
        self.assertEqual(order.paymentType, "online")
        self.assertEqual(order.totalCost, 199.99)
        self.assertEqual(order.status, "accepted")
        self.assertEqual(order.city, "London")
        self.assertEqual(order.address, "221b, Baker str.")
        self.assertEqual(order.profile.fullName, "Test User fullName")

    def test_order_items_creation(self):
        order = Order.objects.create(
            profile=self.profile,
            deliveryType="free",
            paymentType="online",
            totalCost=0,
            status='accepted',
            city="London",
            address="221b, Baker str.",
        )
        order_items = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1
        )
        order.totalCost = sum(item.product.price * item.quantity for item in order.items.all())
        order.save()
        self.assertEqual(float(order.totalCost), 199.99)
        self.assertEqual(order_items.order, order)
        self.assertEqual(order_items.product, self.product)
        self.assertEqual(order_items.quantity, 1)

    def test_order_items_cascade_delete(self):
        order = Order.objects.create(
            profile=self.profile,
            deliveryType="free",
            paymentType="online",
            totalCost=0,
            status='accepted',
            city="London",
            address="221b, Baker str.",
        )
        order_items = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1
        )
        order.delete()
        self.assertFalse(Order.objects.filter(id=order.id).exists())
        self.assertFalse(OrderItem.objects.filter(id=order_items.id).exists())


class OrderDeliveryTypeModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.delivery_type = OrderDeliveryType.objects.create(
            type="express",
            min_cost=Decimal('50.00'),
            delivery_cost=Decimal('5.00')
        )

    def test_order_delivery_type_creation(self):
        delivery_type = OrderDeliveryType.objects.get(id=self.delivery_type.id)
        self.assertEqual(delivery_type.type, "express")
        self.assertEqual(str(delivery_type), "express")
        self.assertEqual(delivery_type.min_cost, Decimal('50.00'))
        self.assertEqual(delivery_type.delivery_cost, Decimal('5.00'))



class PaymentTypeModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.user = User.objects.create(
            username="Test user",
            password="password123"
        )
        cls.profile = Profile.objects.create(
            user=cls.user,
            fullName="Test User fullName"
        )
        cls.order = Order.objects.create(
            profile=cls.profile,
            deliveryType="free",
            paymentType="online",
            totalCost=199.99,
            status='accepted',
            city="London",
            address="221b, Baker str.",
        )

    def test_payment_type_creation(self):
        payment = Payment.objects.create(
            order=self.order,
            number='11111111',
            name="Test User",
            year="1991",
            month="12",
            code="123"
        )
        self.assertEqual(payment.number, "11111111")
        self.assertEqual(payment.name, "Test User")
        self.assertEqual(payment.year, "1991")
        self.assertEqual(payment.month, "12")
        self.assertEqual(payment.code, "123")
        self.assertEqual(payment.order.profile.fullName, "Test User fullName")
        self.assertEqual(payment.order.paymentType, "online")

    def test_payment_cascade_delete(self):
        payment = Payment.objects.create(
            order=self.order,
            number='11111111',
            name="Test User",
            year="1991",
            month="12",
            code="123"
        )
        self.order.delete()
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())
        self.assertFalse(Payment.objects.filter(id=payment.id).exists())


class SaleModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="TV",
            count=14,
            price=199.99,
        )

    def test_sale_creation(self):
        date_from = date(year=2024, month=6, day=1)
        date_to = date(year=2024, month=6, day=30)
        sale = Sale.objects.create(
            product=self.product,
            salePrice=159.99,
            dateFrom=date_from,
            dateTo=date_to
        )
        self.assertEqual(sale.salePrice, 159.99)
        self.assertEqual(sale.dateFrom, date_from)
        self.assertEqual(sale.dateTo, date_to)
        self.assertEqual(sale.product.title, "TV")
        self.assertEqual(str(sale), "TV: 199.99 -> 159.99")

    def test_sale_cascade_delete(self):
        date_from = date(year=2024, month=6, day=1)
        date_to = date(year=2024, month=6, day=30)
        sale = Sale.objects.create(
            product=self.product,
            salePrice=159.99,
            dateFrom=date_from,
            dateTo=date_to
        )
        self.product.delete()
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())
        self.assertFalse(Sale.objects.filter(id=sale.id).exists())


