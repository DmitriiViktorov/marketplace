from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from .cart import Cart
from rest_framework.views import APIView


class CartAPI(APIView):
    """
    API view for interacting with the shopping cart.

    Methods:
        get(request, format=None):
            Retrieves the current state of the shopping cart.

        post(request, **kwargs):
            Adds a product to the shopping cart.

        delete(request, **kwargs):
            Removes a product from the shopping cart.
    """
    def get(self, request: Request, format=None) -> Response:
        """
        Retrieve the current state of the shopping cart.

        :param request: HTTP request object
        :param format: Optional format suffix
        :return: Response with the current products in the cart
        """
        cart = Cart(request)

        return Response(
            cart.get_cart_products(),
            status=status.HTTP_200_OK
        )

    def post(self, request: Request, **kwargs) -> Response:
        """
        Add a product to the shopping cart.

        :param request: HTTP request object containing product data
        :param kwargs: Additional keyword arguments
        :return: Response with the updated products in the cart
        """
        cart = Cart(request)

        product_to_cart = request.data
        cart.add(
                product_id=str(product_to_cart["id"]),
                quantity=int(product_to_cart['count']),
            )
        return Response(
            cart.get_cart_products(),
            status=status.HTTP_200_OK
        )

    def delete(self, request: Request, **kwargs) -> Response:
        """
        Remove a product from the shopping cart.

        :param request: HTTP request object containing product data
        :param kwargs: Additional keyword arguments
        :return: Response with the updated products in the cart
        """
        cart = Cart(request)
        product_to_cart = request.data

        cart.remove(
                product_id=str(product_to_cart["id"]),
                quantity=int(product_to_cart["count"]),
            )
        return Response(
            cart.get_cart_products(),
            status=status.HTTP_200_OK
        )
