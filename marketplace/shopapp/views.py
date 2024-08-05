from datetime import datetime
from typing import Set

from django.urls import reverse
from django.db.models import Count, Avg, QuerySet
from django.db.models.functions import Round
from django_filters import FilterSet
from django_filters.rest_framework import (
    DjangoFilterBackend, NumberFilter,
    BooleanFilter, CharFilter
)

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import Product, Category, Tag, Order, OrderItem, Sale
from .pagination import CustomPagination
from .serializers import (
    CategorySerializer, ProductSerializer, CatalogProductSerializer,
    TagSerializer, ReviewSerializer, OrderSerializer,
    OrderConfirmSerializer, PaymentSerializer, SaleSerializer,
)

from myauth.models import Profile
from cart.cart import Cart


class ProductDetailView(RetrieveAPIView):
    """Product detail view."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CatalogFilter(FilterSet):
    """
    Catalog filter class.
    Adds filtering by price, delivery type, category and rating to the catalog view.
    """
    name = CharFilter(field_name='title', lookup_expr='icontains')
    minPrice = NumberFilter(field_name='price', lookup_expr='gte')
    maxPrice = NumberFilter(field_name='price', lookup_expr='lte')
    freeDelivery = BooleanFilter(field_name='freeDelivery')
    available = BooleanFilter(field_name='available', method='filter_available')
    category = NumberFilter(field_name='category', method='filter_by_category')
    rating = NumberFilter(field_name='average_rating', method='filter_by_rating')

    class Meta:
        model = Product
        fields = [
            'minPrice',
            'maxPrice',
            'freeDelivery',
            'name',
            'category',
            'available',
            'rating'
        ]

    @staticmethod
    def filter_available(queryset: QuerySet[Product], name: str, value: bool) -> QuerySet[Product]:
        """The filter returns a list of products that are in stock"""
        if value:
            return queryset.filter(count__gt=0)
        return queryset

    def filter_by_category(self, queryset: QuerySet[Product], name: str, value: bool) -> QuerySet[Product]:
        """The filter returns a list of products of the selected category"""
        try:
            category = Category.objects.get(id=value)
            subcategories = self.get_all_subcategories(category)
            return queryset.filter(category__in=subcategories)
        except Category.DoesNotExist:
            return queryset.none()

    def get_all_subcategories(self, category: Category) -> Set[Category]:
        """The function adds all subcategories to the filtering by the selected category"""
        subcategories = set()
        categories_to_check = [category]
        while categories_to_check:
            current_category = categories_to_check.pop()
            subcategories.add(current_category)
            categories_to_check.extend(list(current_category.subcategories.all()))
        return subcategories

    def filter_by_rating(self, queryset: QuerySet[Product], name: str, value: bool) -> QuerySet[Product]:
        """The filter returns a list of products by rating"""
        return queryset.filter(average_rating__gte=value)


class CatalogViewSet(ListAPIView):
    """
    Catalog viewset.

    Returns a list of products, taking into account the filtering settings.
    It has an option to sort by fields "price", "date", "reviews" and "rating".
    Pagination is configured in a separate module "pagination".
    """
    queryset = Product.objects.all()
    serializer_class = CatalogProductSerializer
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    ordering_fields = 'price', 'date', 'reviews', 'rating'
    pagination_class = CustomPagination
    filterset_class = CatalogFilter

    def get_queryset(self) -> QuerySet[Product]:
        """Returns a list of products, taking into account filters and sorting"""
        queryset = super().get_queryset().annotate(
            num_reviews=Count('reviews'),
            average_rating=Round(Avg('reviews__rate'), 1),
        ).order_by('id')
        sort = self.request.query_params.get('sort')
        sort_type = self.request.query_params.get('sortType')

        if sort == 'reviews':
            sort = 'num_reviews'
        elif sort == 'rating':
            sort = 'average_rating'

        if sort and sort_type:
            if sort_type == 'inc':
                ordering = sort
            elif sort_type == 'dec':
                ordering = '-' + sort
            queryset = queryset.order_by(ordering)

        return queryset


class CategoryViewSet(ListAPIView):
    """Returns a list of categories."""
    queryset = Category.objects.filter(parent__isnull=True)
    serializer_class = CategorySerializer
    filterset_fields = ['title']
    filter_backends = [DjangoFilterBackend]


class TagListView(ListAPIView):
    """Returns a list of tags."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ReviewView(APIView):
    """View for publishing a new product review."""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Post a new review about the current product"""
        if not request.user.is_authenticated:
            login_url = reverse('myauth:sign-in')
            return Response({
                'detail': 'Authentication required to leave a review.',
                'login_url': login_url
            }, status=status.HTTP_401_UNAUTHORIZED)
        product_id = self.kwargs['pk']
        context = {'product_id': product_id}

        serializer = ReviewSerializer(data=request.data, context=context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PopularProductView(APIView):
    """
    A view for popular products.
    Popularity is determined by the "sort_index" parameter and the number of purchases
    """
    def get(self, request: Request, *args, **kwargs) -> Response:
        products = Product.objects.annotate(
            purchased_count=Count('orderitem')
        ).order_by('-sort_index', '-purchased_count')[:8]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LimitedEditionProductView(APIView):
    """A view for limited products."""
    def get(self, request: Request, *args, **kwargs) -> Response:
        products = Product.objects.filter(limited_edition=True)[:16]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SaleView(ListAPIView):
    """View for products on sale"""
    serializer_class = SaleSerializer
    pagination_class = CustomPagination

    def get_queryset(self) -> QuerySet[Sale]:
        """
        Returns a list of products for which the discount is valid on the day of the order.
        """
        current_date = datetime.now().date()
        return Sale.objects.filter(dateFrom__lte=current_date, dateTo__gte=current_date)


class BannerView(ListAPIView):
    """Returns a list of products for banner."""
    serializer_class = CatalogProductSerializer

    def get_queryset(self) -> QuerySet[Product]:
        return Product.objects.filter(banner=True)


class OrderView(APIView):
    """
    Order view.

    Allows you to get information about all orders of the
    current user and create new orders.
    The order is created from the user's current shopping cart.
    """
    def get(self, request: Request, *args, **kwargs) -> Response:
        """Returns all orders of current user."""
        profile = Profile.objects.get(user=request.user)
        queryset = Order.objects.filter(profile=profile)
        serializer = OrderSerializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Creates a new order.

        Retrieves all products from a form based on cart data.
        Creates a new order associated with the current user.
        Saves all products and their quantity to the OrderItem table.
        Sets the order status as "accepted", clears the cart.
        Returns the ID of the created order.
        """
        products_data = request.data
        cart = Cart(request)

        order = Order.objects.get(pk=request.session['order_id']) \
            if 'order_id' in request.session \
            else Order.objects.create(profile=request.user.profile)

        for product in products_data:
            product_id = product['id']
            quantity = product['count']
            OrderItem.objects.create(
                order=order,
                product=Product.objects.get(id=product_id),
                quantity=quantity,
            )

        order.totalCost = cart.get_cart_total()
        order.status = 'accepted'
        order.save()
        cart.cart.clear()
        cart.save()

        if 'order_id' in request.session:
            del request.session['order_id']

        return Response({'orderId': order.pk}, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """
    Detail view for orders.

    Detailed information about orders can only be viewed by
    authenticated users who created these orders.
    Allows you to view selected orders, as well as add information about
    the payment method and delivery address.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Returns information about current order."""
        order_id = self.kwargs['pk']
        queryset = Order.objects.filter(pk=order_id)
        serializer = OrderSerializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Update current order.

        Update the current order with such information:
        - type of delivery
        - payment type
        - city and delivery address
        - updated order price including delivery
        """
        order_id = self.kwargs['pk']
        order_data = request.data
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.profile != request.user.profile:
            raise PermissionDenied("You do not have permission to update this order.")

        if order.status == 'paid':
            return Response({"detail": "Paid orders cannot be updated."}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderConfirmSerializer(order, data=order_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            order.status = "confirmed"
            order.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentView(APIView):
    """Payment view."""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Creates an order payment record.

        Checks that the order has not been paid yet.
        Checks that the current user is paying for their order.
        """
        order_id = self.kwargs['pk']
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.profile != request.user.profile:
            raise PermissionDenied("You do not have permission to confirm payment for this order.")

        if order.status == 'paid':
            return Response({"detail": "Paid orders cannot be updated."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PaymentSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            order.status = 'paid'
            order.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
