from datetime import datetime, timedelta
from datetime import date

from django.test import TestCase, Client
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from django.contrib.auth.models import User

from .models import (
    Product, Category, ProductImage,
    Tag, ProductTag, Review,
    Order, OrderItem,
    OrderDeliveryType, Sale
)
from .serializers import CategorySerializer, CatalogProductSerializer
from myauth.models import Profile


class ProductViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title='Test Product',
            count=1,
            price=10.00,
        )
        cls.client = Client()

    def test_product_view(self):
        response = self.client.get('/api/product/{}/'.format(str(self.product.id)))
        expected_date = self.product.date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        expected_data = {
            "id": 1,
            'title': "Test Product",
            'count': 1,
            'price': '10.00',
            'date': expected_date,
            'description': None,
            'freeDelivery': False,
            'category': None,
            'images': [],
            'tags': [],
            'rating': None,
            'fullDescription': None,
            "specifications": [],
            'reviews': [],
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.data, expected_data)

    def test_product_not_found(self):
        response = self.client.get('/api/product/2/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_wrong_http_methods(self):
        response = self.client.post('/api/product/{}/'.format(str(self.product.id)))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.put('/api/product/{}/'.format(str(self.product.id)))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.delete('/api/product/{}/'.format(str(self.product.id)))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class CatalogViewTest(TestCase):
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
        cls.another_product = Product.objects.create(
            title="test product 2",
            count=0,
            price=259.99,
            description="short description",
            fullDescription='full description',
            freeDelivery=False,
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
        cls.url = '/api/catalog/'

    def test_catalog_view(self):
        response = self.client.get(f"{self.url}")
        expected_date_1 = self.product.date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        expected_date_2 = self.another_product.date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        expected_data = {
            'items': [
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
                            'src': 'http://testserver/media/test_image.jpg',
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
                    'count': 0,
                    'price': '259.99',
                    'date': expected_date_2,
                    'description': 'short description',
                    'freeDelivery': False,
                    'category': 1,
                    'images': [],
                    'tags': [],
                    'rating': None,
                    'reviews': 0
                }
            ],
            'currentPage': 1,
            'lastPage': 1
            }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.data, expected_data)

    def test_catalog_sorting_price_dec(self):
        response = self.client.get(f"{self.url}?sort=price&sortType=dec")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.data['items'][0]['price'], '259.99')
        self.assertEqual(response.data['items'][1]['title'], 'test product')

    def test_catalog_available(self):
        response = self.client.get(f"{self.url}?available=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(len(response.data['items']), 1)

    def test_filter_by_free_delivery(self):
        response = self.client.get(f"{self.url}?freeDelivery=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['title'], "test product")

    def test_filter_by_category(self):
        response = self.client.get(f"{self.url}?category={self.category.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 2)

    def test_catalog_max_price(self):
        response = self.client.get(f"{self.url}?maxPrice=200")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['title'], "test product")

    def test_catalog_min_price(self):
        response = self.client.get(f"{self.url}?minPrice=200")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['title'], "test product 2")

    def test_catalog_price_not_found(self):
        response = self.client.get(f"{self.url}?minPrice=2000")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)

    def test_catalog_sorting_by_rating(self):
        response = self.client.get(f"{self.url}?sort=rating&sortType=inc")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['title'], "test product 2")


class CategoryViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category1 = Category.objects.create(
            title="Parent category 1",
        )
        cls.category2 = Category.objects.create(
            title="Parent category 2",
        )
        cls.category3 = Category.objects.create(
            title="Child category 1",
            parent=cls.category1,
        )
        cls.url = '/api/categories/'

    def test_get_all_categories(self):
        response = self.client.get(self.url)
        categories = Category.objects.filter(parent__isnull=True)
        serializer = CategorySerializer(categories, many=True)
        titles = [category['title'] for category in response.data]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 2)
        self.assertNotIn("Child category 1", titles)

    def test_filter_categories_by_title(self):
        response = self.client.get(f"{self.url}?title=Parent category 1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Parent category 1")

    def test_filter_categories_no_results(self):
        response = self.client.get(f"{self.url}?title=NonexistentCategory")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_category_structure(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category = response.data[0]
        self.assertIn('id', category)
        self.assertIn('title', category)
        self.assertIn('image', category)
        self.assertIn('subcategories', category)


class TagListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tag1 = Tag.objects.create(
            name="Tag 1",
        )
        cls.tag2 = Tag.objects.create(
            name="Tag 2",
        )
        cls.url = '/api/tags/'

    def test_get_all_tags(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn("Tag 1", response.data[0]['name'])

    def test_tags_wrong_methods(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ReviewViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.user = User.objects.create(
            username="testuser",
            password="<PASSWORD>",
        )
        cls.profile = Profile.objects.create(
            user=cls.user,
            fullName="John Doe",
            email="john@example.com",
        )
        cls.product = Product.objects.create(
            title="Test product",
            count=1,
            price=10.00
        )
        cls.url = '/api/product/{}/reviews'.format(cls.product.id)

    def test_get_add_review(self):
        self.api_client.force_authenticate(user=self.user)
        data = {
            'author': self.profile,
            'email': self.profile.email,
            'text': 'Great product!',
            'rate': 5,
            'date': datetime.now()
        }
        response = self.api_client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.get().text, 'Great product!')

    def test_create_review_unauthenticated(self):
        data = {
            'author': self.profile,
            'email': self.profile.email,
            'text': 'Great product!',
            'rate': 5,
            'date': datetime.now()
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Authentication credentials were not provided.', response.data['detail'])

    def test_get_add_review_invalid_data(self):
        self.api_client.force_authenticate(user=self.user)
        data = {
            'author': self.profile,
            'email': self.profile.email,
            'text': 'Great product!',
            'rate': 6,
            'date': datetime.now()
        }
        response = self.api_client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_review_nonexistent_product(self):
        url = '/api/product/2/reviews'
        self.api_client.force_authenticate(user=self.user)
        data = {
            'author': self.profile,
            'email': self.profile.email,
            'text': 'Great product!',
            'rate': 5,
            'date': datetime.now()
        }
        response = self.api_client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PopularProductViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product1 = Product.objects.create(
            title="Test product 1",
            count=1,
            price=10.00,
            sort_index=1
        )
        cls.product2 = Product.objects.create(
            title="Test product 2",
            count=1,
            price=10.00,
            sort_index=2
        )
        cls.url = "/api/products/popular/"

    def test_get_all_popular_products(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn("Test product 2", response.data[0]['title'])

    def test_get_eight_products(self):
        for i in range(3, 12):
            Product.objects.create(
                title="Test product {}".format(i),
                count=1,
                price=10.00
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 8)
        self.assertIn("Test product 2", response.data[0]['title'])


class LimitedEditionProductView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product1 = Product.objects.create(
            title="Test product 1",
            count=1,
            price=10.00,
            limited_edition=True
        )
        cls.product2 = Product.objects.create(
            title="Test product 2",
            count=1,
            price=10.00,
            limited_edition=False
        )
        cls.url = "/api/products/limited/"

    def test_get_limited_edition_products(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("Test product 1", response.data[0]['title'])

    def test_get_seventeen_products(self):
        for i in range(3, 20):
            Product.objects.create(
                title="Test product {}".format(i),
                count=1,
                price=10.00,
                limited_edition=True
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 16)
        self.assertIn("Test product 1", response.data[0]['title'])


class SaleViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product1 = Product.objects.create(
            title="Test product 1",
            count=1,
            price=10.00,
        )
        cls.current_date = date.today()
        cls.sale_1 = Sale.objects.create(
            product=cls.product1,
            salePrice=(cls.product1.price * 0.9),
            dateFrom=cls.current_date - timedelta(days=2),
            dateTo=cls.current_date + timedelta(days=2),
        )
        cls.url ="/api/sales/"

    def test_get_sale(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertIn("Test product 1", response.data["items"][0]['title'])

    def test_missed_sale(self):
        sale_2 = Sale.objects.create(
            product=self.product1,
            salePrice=(self.product1.price * 0.9),
            dateFrom=self.current_date - timedelta(days=10),
            dateTo=self.current_date - timedelta(days=5),
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)


class BannerViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product1 = Product.objects.create(
            title="Test product 1",
            count=1,
            price=10.00,
            banner=True
        )
        cls.product2 = Product.objects.create(
            title="Test product 2",
            count=1,
            price=10.00,
            banner=False
        )
        cls.url = "/api/banners/"

    def test_get_banner_products(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("Test product 1", response.data[0]['title'])

    def test_no_banner_products(self):
        self.product1.banner = False
        self.product1.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class OrderViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.user = User.objects.create_user(username='testuser', password='12345')
        cls.profile = Profile.objects.create(user=cls.user, fullName='test user profile')
        cls.product1 = Product.objects.create(
            title="Test product 1",
            count=10,
            price=10.00,
        )
        cls.product2 = Product.objects.create(
            title="Test product 2",
            count=10,
            price=30.00,
        )
        cls.url = "/api/orders"

    def test_get_empty_orders(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_post_and_get_orders(self):
        self.api_client.force_authenticate(user=self.user)
        session = self.api_client.session
        product_1_data = dict(CatalogProductSerializer(self.product1).data)
        product_1_data['count'] = 2
        product_2_data = dict(CatalogProductSerializer(self.product2).data)
        product_2_data['count'] = 1

        session['cart'] = {
            "items": [
                {
                 "product_id": self.product1.id,
                 "product_data": product_1_data
                },
                {
                 "product_id": self.product2.id,
                 "product_data": product_2_data
                }
            ]
        }
        session.save()
        data = [
            {'id': self.product1.id, 'count': 2},
            {'id': self.product2.id, 'count': 1}
        ]
        response = self.api_client.post(self.url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('orderId', response.data)

        order = Order.objects.get(pk=response.data['orderId'])
        self.assertEqual(order.status, 'accepted')
        self.assertEqual(order.totalCost, 50.00)

        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), 2)

        self.assertEqual(self.api_client.session['cart'], {})

        get_response = self.api_client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data[0]['fullName'], 'test user profile')
        self.assertEqual(len(get_response.data[0]['products']), 2)
        self.assertEqual(get_response.data[0]['totalCost'], '50.00')

    def test_create_order_empty_cart(self):
        self.api_client.force_authenticate(user=self.user)

        data = []
        response = self.api_client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('orderId', response.data)

        order = Order.objects.get(pk=response.data['orderId'])
        self.assertEqual(order.status, 'accepted')
        self.assertEqual(order.totalCost, 0)


class OrderDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.user = User.objects.create_user(username='testuser', password='12345')
        cls.profile = Profile.objects.create(user=cls.user, fullName='test user profile')
        cls.product1 = Product.objects.create(
            title="Test product 1",
            count=10,
            price=10.00,
        )
        cls.order = Order.objects.create(
            profile=cls.profile,
            deliveryType="",
            paymentType="",
            totalCost=50.00,
            status="accepted",
            city="",
            address=""
        )
        cls.orderitems = OrderItem.objects.create(
            order=cls.order,
            product=cls.product1,
            quantity=5
        )
        cls.delivery_type = OrderDeliveryType.objects.create(
            type="free",
            min_cost=1000,
            delivery_cost=200.00
        )
        cls.url = "/api/order/{}".format(cls.order.pk)

    def test_get_order_details(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data[0]["fullName"], "test user profile")
        self.assertEqual(len(response.data[0]["products"]), 1)

    def test_get_order_detail_unauthorized(self):
        response = self.api_client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_order_details(self):
        self.api_client.force_authenticate(user=self.user)
        data = {
            "deliveryType": "free",
            "paymentType": "online",
            "city": "London",
            "address": "221b, Bakers str.",
            "totalCost": 500,
            "status": "accepted",
        }
        response = self.api_client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.order.address, "221b, Bakers str.")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "confirmed")

    def test_post_order_detail_unauthorized(self):
        response = self.api_client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_incorrect_order_id(self):
        self.api_client.force_authenticate(user=self.user)
        url = "/api/order/2"
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"detail": "Order not found."})

    def test_post_incorrect_delivery_type(self):
        self.api_client.force_authenticate(user=self.user)
        data = {
            "deliveryType": "express",
        }
        response = self.api_client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_message = str(response.data['non_field_errors'][0])
        self.assertIn("Unsupported delivery type: express", error_message)

    def test_post_incorrect_user(self):
        another_user = User.objects.create_user(username='testuser2', password='<PASSWORD>')
        another_profile = Profile.objects.create(user=another_user, fullName='another user profile')
        self.api_client.force_authenticate(user=another_user)
        response = self.api_client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(response.data["detail"],  "You do not have permission to update this order.")

    def test_post_paid_order(self):
        self.api_client.force_authenticate(user=self.user)
        new_order = Order.objects.create(
            profile=self.profile,
            deliveryType="",
            paymentType="",
            totalCost=50.00,
            status="paid",
            city="",
            address=""
        )
        url = "/api/order/2"
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Paid orders cannot be updated."})


class PaymentViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.api_client = APIClient()
        cls.user = User.objects.create_user(username='testuser', password='12345')
        cls.profile = Profile.objects.create(user=cls.user, fullName='test user profile')
        cls.order = Order.objects.create(
            profile=cls.profile,
            deliveryType="",
            paymentType="",
            totalCost=50.00,
            status="confirmed",
            city="",
            address=""
        )
        cls.url = "/api/payment/{}".format(cls.order.id)

    def test_post_payment_details(self):
        self.api_client.force_authenticate(user=self.user)
        data = {
            "number": "12345678",
            "name": "Annoying Orange",
            "month": "02",
            "year": "2025",
            "code": "123"
        }
        response = self.api_client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    def test_post_payment_details_unauthenticated(self):
        data = {
            "number": "12345678",
            "name": "Annoying Orange",
            "month": "02",
            "year": "2025",
            "code": "123"
        }
        response = self.api_client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_payment_details_wrong_user(self):
        other_user = User.objects.create_user(username='testuser2', password='<PASSWORD>')
        other_user_profile = Profile.objects.create(user=other_user, fullName='another user profile')
        self.api_client.force_authenticate(user=other_user)
        data = {
            "number": "12345678",
            "name": "Annoying Orange",
            "month": "02",
            "year": "2025",
            "code": "123"
        }
        response = self.api_client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(response.data['detail'], "You do not have permission to confirm payment for this order.")

    def test_post_payment_details_already_paid(self):
        self.order.status = 'paid'
        self.order.save()
        self.api_client.force_authenticate(user=self.user)
        data = {
            "number": "12345678",
            "name": "Annoying Orange",
            "month": "02",
            "year": "2025",
            "code": "123"
        }
        response = self.api_client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Paid orders cannot be updated."})

    def test_post_payment_details_invalid_data(self):
        self.api_client.force_authenticate(user=self.user)
        data = {
            "number": "12345678",
            "name": "Annoying Orange",
            "month": "13",
            "year": "2025",
            "code": "123"
        }
        response = self.api_client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response.data['month'][0], "Expiry month must be a number between 01 and 12.")

    def test_post_payment_details_order_not_found(self):
        self.api_client.force_authenticate(user=self.user)
        url = "/api/payment/99999"
        data = {
            "number": "12345678",
            "name": "Annoying Orange",
            "month": "02",
            "year": "2025",
            "code": "123"
        }
        response = self.api_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"detail": "Order not found."})
