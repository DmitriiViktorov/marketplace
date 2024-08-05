from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from shopapp.models import Product

from .cart import Cart


class CartAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        cls.product1 = Product.objects.create(
            title="Product 1",
            price=10.00,
            count=100
        )
        cls.product2 = Product.objects.create(
            title="Product 2",
            price=20.00,
            count=50
        )
        cls.cart_url = "/api/basket"

    def setUp(self):
        self.client = APIClient()
        self.client.login(username="testuser", password="testpassword")

    def test_get_cart(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_add_product_to_cart(self):
        response = self.client.post(self.cart_url, {
            "id": str(self.product1.id),
            "count": 2,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Product 1")
        self.assertEqual(response.data[0]['count'], 2)
        self.assertEqual(response.data[0]['price'], '10.00')

    def test_remove_product_from_cart(self):
        self.client.post(self.cart_url, {
            "id": str(self.product1.id),
            "count": 2,
        })
        response = self.client.delete(self.cart_url, {
            "id": str(self.product1.id),
            "count": 1,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['count'], 1)

        response = self.client.delete(self.cart_url, {
            "id": str(self.product1.id),
            "count": 1,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_clear_cart(self):
        self.client.post(self.cart_url, {
            "id": str(self.product1.id),
            "count": 2,
        })
        self.client.post(self.cart_url, {
            "id": str(self.product2.id),
            "count": 1,
        })

        response = self.client.get('/')
        request = response.wsgi_request
        cart = Cart(request)
        cart.clear()
        self.assertEqual(len(cart.get_cart_products()), 0)

    def tearDown(self):
        self.client.logout()
