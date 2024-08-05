from decimal import Decimal

from django.conf import settings
from rest_framework.request import Request
from shopapp.models import Product
from shopapp.serializers import CatalogProductSerializer


class Cart:
    """
    A shopping cart implementation.

    Attributes:
        session (django.contrib.sessions.backends.base.SessionBase): The session object.
        cart (dict): The cart data stored in the session.
    """

    def __init__(self, request: Request):
        """
         Initialize the cart.

         Args:
             request (django.http.HttpRequest): The HTTP request object.
         """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {'items': []}
        self.cart = cart

    def __str__(self):
        """
        Return a string representation of the cart.

        Returns:
            str: String representation of the cart.
        """
        return str(self.cart)

    def add(self, product_id: str, quantity: int):
        """
        Add a product to the cart or increase its quantity if already present.

        Args:
            product_id (str): The ID of the product to add.
            quantity (int): The quantity of the product to add.
        """
        for item in self.cart['items']:
            if item['product_id'] == product_id:
                item['product_data']['count'] += quantity
                self.save()
                return

        product = Product.objects.get(pk=product_id)
        product_data = dict(CatalogProductSerializer(product).data)
        product_data['count'] = quantity
        self.cart['items'].append({'product_id': product_id, 'product_data': product_data})
        self.save()

    def remove(self, product_id: str, quantity: int):
        """
        Remove a product from the cart or decrease its quantity.

        Args:
            product_id (str): The ID of the product to remove.
            quantity (int): The quantity of the product to remove.
        """
        for item in self.cart['items']:
            if item['product_id'] == product_id:
                item['product_data']['count'] -= quantity
                if item['product_data']['count'] <= 0:
                    self.cart['items'].remove(item)
                self.save()

    def save(self):
        """Save the cart data to the session."""
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def clear(self):
        """Clear all items from the cart."""
        self.cart['items'] = []
        self.save()

    def get_cart_products(self):
        """
        Get a list of products in the cart.

        Returns:
            list: A list of product data dictionaries.
        """
        return [item['product_data'] for item in self.cart['items']]

    def get_cart_total(self):
        """
        Calculate the total cost of all items in the cart.

        Returns:
            Decimal: The total cost of all items in the cart.
        """
        total = Decimal(0)
        for item in self.cart['items']:
            price = Decimal(item['product_data']['price'])
            count = item['product_data']['count']
            total += price * count
        return total
