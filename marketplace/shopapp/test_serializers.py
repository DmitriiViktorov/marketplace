import os
from datetime import date

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Count, Avg
from django.db.models.functions import Round
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APITestCase

from .models import (
    Product, Category, ProductImage,
    Tag, ProductTag, Review,
    Specification, Order, OrderItem,
    OrderDeliveryType, Payment, Sale
)
from .serializers import (
    CategorySerializer, ProductSerializer, CatalogProductSerializer,
    TagSerializer, ReviewSerializer, OrderSerializer,
    OrderConfirmSerializer, PaymentSerializer, SaleSerializer,
    ProductImageSerializer, SpecificationSerializer,
)
from myauth.models import Profile


class ProductImageSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="test product",
            count=10,
            price=159.99
        )
        cls.product_image = ProductImage.objects.create(
            product=cls.product,
            src='test_image.jpg',
            alt='Test image'
        )
        cls.image_path = 'shopapp/test_images/default_image.png'
        with open(cls.image_path, 'rb') as image_file:
            cls.uploaded_image = SimpleUploadedFile(
                name='default_image.png',
                content=image_file.read(),
                content_type='image/png'
            )

    def test_serialization(self):
        serializer = ProductImageSerializer(instance=self.product_image)
        data = serializer.data
        expected_data = {
            "src": "/media/test_image.jpg",
            "alt": "Test image",
        }
        self.assertEqual(data, expected_data)

    def test_deserialization(self):
        image_data = {
            "src": self.uploaded_image,
            "alt": "Test image",
        }
        serializer = ProductImageSerializer(data=image_data)
        self.assertTrue(serializer.is_valid())
        product_image = serializer.save(product=self.product)
        self.assertEqual(product_image.src.name.split('/')[-1], self.uploaded_image.name)
        self.assertEqual(product_image.alt, "Test image")

    def tearDown(self):
        for product_image in ProductImage.objects.all():
            if product_image.src:
                if os.path.isfile(product_image.src.path):
                    os.remove(product_image.src.path)


class TagSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tag = Tag.objects.create(
            name="test tag",
        )

    def test_serialization(self):
        serializer = TagSerializer(instance=self.tag)
        data = serializer.data
        expected_data = {
            "id": 1,
            "name": "test tag",
        }
        self.assertEqual(data, expected_data)

    def test_deserialization(self):
        data = {
            'name': 'test tag',
        }
        serializer = TagSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        tag = serializer.save()
        self.assertEqual(tag.id, 2)
        self.assertEqual(tag.name, 'test tag')


class SpecificationSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="test product",
            count=10,
            price=159.99
        )

        cls.specification = Specification.objects.create(
            product=cls.product,
            name="Test name",
            value="Test value",
        )

    def test_serialization(self):
        serializer = SpecificationSerializer(instance=self.specification)
        expected_data = {
            "name": "Test name",
            "value": "Test value",
        }
        self.assertEqual(serializer.data, expected_data)

    def test_deserialization(self):
        data = {
            "name": "Test name",
            "value": "Test value",
        }
        serializer = SpecificationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        specification = serializer.save(product=self.product)
        self.assertEqual(specification.name, 'Test name')
        self.assertEqual(specification.value, 'Test value')


class ReviewSerializerTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Test Product",
            count=10,
            price=99.99
        )
        cls.review = Review.objects.create(
            product=cls.product,
            author="John Doe",
            email="john@example.com",
            text="Great product!",
            rate=5,
            date=timezone.now()
        )

    def test_serialization(self):
        serializer = ReviewSerializer(instance=self.review)
        data = serializer.data
        expected_date = self.review.date.strftime('%Y-%m-%d %H:%M')
        expected_data = {
            'author': self.review.author,
            'email': self.review.email,
            'text': self.review.text,
            'rate': self.review.rate,
            'date': expected_date,
        }
        self.assertEqual(data, expected_data)

    def test_deserialization(self):
        data = {
            'author': 'Jane Doe',
            'email': 'jane@example.com',
            'text': 'Not bad',
            'rate': 4,
            'date': timezone.now().strftime('%Y-%m-%d %H:%M'),
        }
        serializer = ReviewSerializer(data=data, context={'product_id': self.product.id})
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        review = serializer.save()
        self.assertEqual(review.author, data['author'])
        self.assertEqual(review.email, data['email'])
        self.assertEqual(review.text, data['text'])
        self.assertEqual(review.rate, data['rate'])
        self.assertEqual(review.product, self.product)

    def test_validation(self):
        data = {
            'author': '',
            'email': 'not-an-email',
            'text': '',
            'rate': 10,
            'date': timezone.now().strftime('%Y-%m-%d %H:%M'),
        }
        serializer = ReviewSerializer(data=data, context={'product_id': self.product.id})
        self.assertFalse(serializer.is_valid())
        self.assertIn('author', serializer.errors)
        self.assertIn('email', serializer.errors)
        self.assertIn('text', serializer.errors)
        self.assertIn('rate', serializer.errors)


class BaseProductSerializer(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.datestamp = timezone.now()
        cls.another_datestamp = timezone.now() + timezone.timedelta(days=1)
        cls.category = Category.objects.create(
            title="Electronics"
        )
        cls.tag = Tag.objects.create(
            name="test tag",
        )

        cls.product = Product.objects.create(
            title="test product",
            count=10,
            price=159.99,
            description="short description",
            fullDescription='full description',
            freeDelivery=True,
            category=cls.category,
        )
        cls.product_tag = ProductTag.objects.create(
            product=cls.product,
            tag=cls.tag,
        )
        cls.review = Review.objects.create(
            product=cls.product,
            author="John Doe",
            email="john@example.com",
            text="Great product!",
            rate=5,
            date=cls.datestamp,
        )
        cls.another_review = Review.objects.create(
            product=cls.product,
            author="John Smith",
            email="smith@example.com",
            text="Awful product!",
            rate=1,
            date=cls.another_datestamp,
        )
        cls.product_image = ProductImage.objects.create(
            product=cls.product,
            src='test_image.jpg',
            alt='Test image'
        )


class ProductSerializerTests(BaseProductSerializer):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.specification = Specification.objects.create(
            product=cls.product,
            name="Test name",
            value="Test value",
        )

    def test_serialization(self):
        serializer = ProductSerializer(instance=self.product)
        data = serializer.data
        expected_date = self.product.date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        expected_data = {
            "id": 1,
            'title': "test product",
            'count': 10,
            'price': '159.99',
            'date': expected_date,
            'description': "short description",
            'fullDescription': "full description",
            'freeDelivery': True,
            'category': 1,
            'images': [{
                "src": "/media/test_image.jpg",
                "alt": "Test image",
            }],
            'tags': [
                {
                    "id": 1,
                    "name": "test tag",
                }
            ],
            'reviews': [
                {
                    "author": "John Smith",
                    "email": "smith@example.com",
                    "text": "Awful product!",
                    "rate": 1,
                    "date": self.datestamp.strftime('%Y-%m-%d %H:%M'),
                },
                {
                    "author": "John Doe",
                    "email": "john@example.com",
                    "text": "Great product!",
                    "rate": 5,
                    "date": self.datestamp.strftime('%Y-%m-%d %H:%M'),
                }
            ],
            "specifications": [
                {
                    "name": "Test name",
                    "value": "Test value",
                }
            ],
            'rating': 3.0
        }
        self.assertEqual(data, expected_data)

    def test_deserialization(self):
        data = {
            'title': "new product",
            'count': 5,
            'price': '299.99',
            'description': "short description",
            'fullDescription': "full description",
            'freeDelivery': True,
            'category': self.category.id,
        }
        serializer = ProductSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        product = serializer.save()
        self.assertEqual(product.title, "new product")
        self.assertEqual(product.count, 5)
        self.assertEqual(float(product.price), 299.99)
        self.assertEqual(product.description, "short description")
        self.assertEqual(product.fullDescription, "full description")
        self.assertEqual(product.freeDelivery, True)
        self.assertEqual(product.category, self.category)

    def test_validation(self):
        data = {
            'title': "",
            'count': -1,
            'price': '-299.99',
            'description': "",
            'freeDelivery': True,
            'category': self.category.id,
        }
        serializer = ProductSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertIn('count', serializer.errors)
        self.assertIn('price', serializer.errors)
        self.assertNotIn('description', serializer.errors)
        self.assertNotIn('fullDescription', serializer.errors)


class CatalogSerializerTests(BaseProductSerializer):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.another_product = Product.objects.create(
            title="test product 2",
            count=20,
            price=259.99,
            description="short description",
            fullDescription='full description',
            freeDelivery=True,
            category=cls.category,
        )

    def test_serialization(self):
        annotated_products = Product.objects.annotate(
            num_reviews=Count('reviews'),
            average_rating=Round(Avg('reviews__rate'), 1)
        ).all()
        serializer = CatalogProductSerializer(annotated_products, many=True)
        data = serializer.data
        expected_date_1 = self.product.date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        expected_date_2 = self.another_product.date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        expected_data = [
            {
                'id': 1,
                'title': 'test product',
                'count': 10,
                'price': '159.99',
                'date': expected_date_1,
                'description': 'short description',
                'freeDelivery': True,
                'category': 1,
                'images': [
                     {
                        'src': '/media/test_image.jpg',
                        'alt': 'Test image'
                     }
                ],
                'tags': [
                    {
                        'id': 1,
                        'name': 'test tag'
                    }
                ],
                'rating': 3.0,
                'reviews': 2
             },
            {
                'id': 2,
                'title': 'test product 2',
                'count': 20,
                'price': '259.99',
                'date': expected_date_2,
                'description': 'short description',
                'freeDelivery': True,
                'category': 1,
                'images': [],
                'tags': [],
                'rating': None,
                'reviews': 0,
            }

        ]

        self.assertEqual(data, expected_data)


class CategorySerializerTests(BaseProductSerializer):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            title="test category",
        )
        cls.image_path = 'shopapp/test_images/default_image.png'
        with open(cls.image_path, 'rb') as image_file:
            cls.uploaded_image = SimpleUploadedFile(
                name='default_image.png',
                content=image_file.read(),
                content_type='image/png'
            )

    def test_serialization(self):
        serializer = CategorySerializer(instance=self.category)
        data = serializer.data
        expected_data = {
            "id": 1,
            "title": "test category",
            "image": {
                "src": None,
                "alt": "",
            },
            "subcategories": [],
        }
        self.assertEqual(data, expected_data)

    def test_serialization_with_image(self):
        self.category.src = self.uploaded_image
        self.category.save()
        serializer = CategorySerializer(instance=self.category)
        data = serializer.data
        self.assertIsNotNone(data['image']['src'])
        self.assertIn('default_image.png', data['image']['src'])

    def test_deserialization(self):
        data = {
            "title": "New Category",
            "image": self.uploaded_image,
        }
        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.title, "New Category")
        self.assertIsNotNone(category.src)

    def test_serialization_with_subcategories(self):
        subcategory = Category.objects.create(title="Subcategory", parent=self.category)
        serializer = CategorySerializer(instance=self.category)
        data = serializer.data
        self.assertEqual(len(data['subcategories']), 1)
        self.assertEqual(data['subcategories'][0]['title'], "Subcategory")

    def tearDown(self):
        for category_image in Category.objects.all():
            if category_image.src:
                if os.path.isfile(category_image.src.path):
                    os.remove(category_image.src.path)


class BaseOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product_1 = Product.objects.create(
            title="TV",
            count=1,
            price=199.99,
        )
        cls.product_2 = Product.objects.create(
            title="Laptop",
            count=1,
            price=299.99,
        )
        cls.user = User.objects.create(
            username="Test user",
            password="password123"
        )
        cls.profile = Profile.objects.create(
            user=cls.user,
            fullName="Test User fullName",
            phone="88805553535",
            email="user@example.com"
        )
        cls.order = Order.objects.create(
            profile=cls.profile,
            totalCost=0,
            status='accepted',

        )
        OrderItem.objects.create(
            order=cls.order,
            product=cls.product_1,
            quantity=1
        )
        OrderItem.objects.create(
            order=cls.order,
            product=cls.product_2,
            quantity=1
        )


class OrderSerializerTests(BaseOrderTests):

    def test_serialization(self):
        serializer = OrderSerializer(instance=self.order)
        data = serializer.data
        expected_date = self.order.createdAt.strftime('%Y-%m-%d %H:%M')
        product_date_1 = self.product_1.date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        product_date_2 = self.product_2.date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        expected_data = {
            "id": 1,
            "createdAt": expected_date,
            "fullName": self.profile.fullName,
            "email": "user@example.com",
            "phone": "88805553535",
            "deliveryType": "",
            "paymentType": "",
            "address": "",
            "city": "",
            "totalCost": "0.00",
            "status": "accepted",
            "products": [
                {
                    "id": 1,
                    "title": "TV",
                    "count": 1,
                    "price": "199.99",
                    "date": product_date_1,
                    "description": None,
                    "freeDelivery": False,
                    "category": None,
                    "images": [],
                    "tags": [],
                },
                {
                    "id": 2,
                    "title": "Laptop",
                    "count": 1,
                    "price": "299.99",
                    "date": product_date_2,
                    "description": None,
                    "freeDelivery": False,
                    "category": None,
                    "images": [],
                    "tags": [],
                }
            ]
        }
        self.assertEqual(data, expected_data)

    def test_order_update(self):
        data = {
            "status": "delivered",
            "address": "Updated Address"
        }
        serializer = OrderSerializer(instance=self.order, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_order = serializer.save()
        self.assertEqual(updated_order.status, "delivered")
        self.assertEqual(updated_order.address, "Updated Address")

    def test_profile_fields_read_only(self):
        data = {
            "fullName": "New Name",
            "phone": "99999999",
            "email": "new@email.com"
        }
        serializer = OrderSerializer(instance=self.order, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_order = serializer.save()

        self.assertEqual(updated_order.profile.fullName, self.profile.fullName)
        self.assertEqual(updated_order.profile.phone, self.profile.phone)
        self.assertEqual(updated_order.profile.email, self.profile.email)


class OrderConfirmSerializerTests(BaseOrderTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.deliveryType = OrderDeliveryType.objects.create(
            type="free",
            min_cost=2000,
            delivery_cost=200
        )

    def test_serialization_with_delivery_cost(self):
        total_cost_before = 1999.00
        new_data = {
            "deliveryType": "free",
            "paymentType": "online",
            "address": "221b, Baker str.",
            "city": "London",
            "totalCost": total_cost_before,
        }
        serializer = OrderConfirmSerializer(instance=self.order, data=new_data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(float(serializer.data["totalCost"]), (total_cost_before + self.deliveryType.delivery_cost))

    def test_serialization_without_delivery_cost(self):
        total_cost_before = 2999.00
        new_data = {
            "deliveryType": "free",
            "paymentType": "online",
            "address": "221b, Baker str.",
            "city": "London",
            "totalCost": total_cost_before,
        }
        serializer = OrderConfirmSerializer(instance=self.order, data=new_data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(float(serializer.data["totalCost"]), total_cost_before)

    def test_serialization_wrong_delivery_type(self):
        total_cost_before = 2999.00
        new_data = {
            "deliveryType": "express",
            "paymentType": "online",
            "address": "221b, Baker str.",
            "city": "London",
            "totalCost": total_cost_before,
        }
        serializer = OrderConfirmSerializer(instance=self.order, data=new_data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        error_message = str(serializer.errors['non_field_errors'][0])
        self.assertIn("Unsupported delivery type: express", error_message)


class PaymentSerializerTests(BaseOrderTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.payment = Payment.objects.create(
            order=cls.order,
            number="11112222",
            name="Annoying Orange",
            month="02",
            year="2025",
            code="123"
        )

    def test_serialization(self):
        serializer = PaymentSerializer(instance=self.payment)
        data = serializer.data
        expected_data = {
            "number": "11112222",
            "name": "Annoying Orange",
            "month": "02",
            "year": "2025",
            "code": "123"
        }
        self.assertEqual(data, expected_data)

    def test_deserialization(self):
        data = {
            "number": "11112222",
            "name": "Annoying Orange",
            "month": "02",
            "year": "2025",
            "code": "123"
        }
        serializer = PaymentSerializer(data=data, context={'order': self.order})
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.data["number"], "11112222")
        self.assertEqual(serializer.data["name"], "Annoying Orange")

    def test_payment_wrong_year(self):
        data = {
            "number": "11112222",
            "name": "Annoying Orange",
            "month": "02",
            "year": "25",
            "code": "123"
        }
        serializer = PaymentSerializer(data=data, context={'order': self.order})
        self.assertFalse(serializer.is_valid())
        self.assertIn('year', serializer.errors)
        error_message = str(serializer.errors['year'][0])
        self.assertEqual("Expiry year must be a 4-digit number.", error_message)

    def test_payment_wrong_month(self):
        data = {
            "number": "11112222",
            "name": "Annoying Orange",
            "month": "13",
            "year": "2025",
            "code": "123"
        }
        serializer = PaymentSerializer(data=data, context={'order': self.order})
        self.assertFalse(serializer.is_valid())
        self.assertIn('month', serializer.errors)
        error_message = str(serializer.errors['month'][0])
        self.assertEqual("Expiry month must be a number between 01 and 12.", error_message)

    def test_payment_wrong_code(self):
        data = {
            "number": "11112222",
            "name": "Annoying Orange",
            "month": "13",
            "year": "2025",
            "code": "12345"
        }
        serializer = PaymentSerializer(data=data, context={'order': self.order})
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)
        error_message = str(serializer.errors['code'][0])
        self.assertEqual("Ensure this field has no more than 4 characters.", error_message)

    def test_payment_wrong_code_as_string(self):
        data = {
            "number": "11112222",
            "name": "Annoying Orange",
            "month": "13",
            "year": "2025",
            "code": "code"
        }
        serializer = PaymentSerializer(data=data, context={'order': self.order})
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)
        error_message = str(serializer.errors['code'][0])
        self.assertEqual("CVV must be a 3 or 4-digit number.", error_message)


class SaleSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Product title",
            count=1,
            price=5.00,
        )
        cls.date_from = date(year=2024, month=6, day=1)
        cls.date_to = date(year=2024, month=6, day=30)
        cls.sale = Sale.objects.create(
            product=cls.product,
            salePrice=(cls.product.price * 0.9),
            dateFrom=cls.date_from,
            dateTo=cls.date_to
        )

    def test_serialization(self):
        serializer = SaleSerializer(instance=self.sale)
        data = serializer.data
        expected_data = {
            "salePrice": "4.50",
            "dateFrom": "06-01",
            "dateTo": "06-30",
            "id": 1,
            "price": "5.00",
            "title": "Product title",
            "images": []
        }

        self.assertEqual(data, expected_data)

    def test_multiple_sales_serialization(self):
        Sale.objects.create(
            product=self.product,
            salePrice=4.00,
            dateFrom=date(2024, 7, 1),
            dateTo=date(2024, 7, 31)
        )
        sales = Sale.objects.all()
        serializer = SaleSerializer(sales, many=True)
        self.assertEqual(len(serializer.data), 2)
        self.assertEqual(serializer.data[0]["salePrice"], "4.50")
        self.assertEqual(serializer.data[1]["salePrice"], "4.00")
