from django.db.models import Avg
from rest_framework import serializers

from .models import (
    Category, Product, ProductImage,
    Tag, Review, Specification,
    Order, OrderItem, OrderDeliveryType,
    Payment, Sale
)

from myauth.models import Profile


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images"""
    class Meta:
        model = ProductImage
        fields = ('src', 'alt')


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags"""
    class Meta:
        model = Tag
        fields = ('id', 'name')


class SpecificationSerializer(serializers.ModelSerializer):
    """Serializer for specifications"""
    class Meta:
        model = Specification
        fields = ('name', 'value')


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviews"""
    class Meta:
        model = Review
        fields = ('author', 'email', 'text', 'rate', 'date')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        date_format = '%Y-%m-%d %H:%M'
        representation['date'] = instance.date.strftime(date_format)
        return representation

    def create(self, validated_data):
        product_id = self.context['product_id']
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError(f"Not found product with id: {product_id}")
        return Review.objects.create(product=product, **validated_data)


class BaseProductSerializer(serializers.ModelSerializer):
    """Base product serializer"""
    images = ProductImageSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'title',
            'count',
            'price',
            'date',
            'description',
            'freeDelivery',
            'category',
            'images',
            'tags',
            'rating'
        )

    def get_tags(self, obj: Product):
        tags = Tag.objects.filter(producttag__product=obj)
        return TagSerializer(tags, many=True).data

    def get_rating(self, obj: Product):
        rating = Review.objects.filter(product=obj).aggregate(Avg('rate'))['rate__avg']
        return round(rating, 1) if rating else None


class ProductSerializer(BaseProductSerializer):
    """Detailed product serializer for product views"""
    specifications = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + ('fullDescription', 'specifications', 'reviews')

    def get_specifications(self, obj: Product):
        specifications = Specification.objects.filter(product=obj)
        return SpecificationSerializer(specifications, many=True).data

    def get_reviews(self, obj: Product):
        reviews = Review.objects.filter(product=obj)
        return ReviewSerializer(reviews, many=True).data


class CatalogProductSerializer(BaseProductSerializer):
    """Detailed product serializer for catalog views"""
    reviews = serializers.IntegerField(source='num_reviews', read_only=True)
    rating = serializers.FloatField(source='average_rating', read_only=True)

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + ('reviews', 'rating')


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories"""
    image = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'title', 'image', 'subcategories')

    def get_image(self, obj: Category):
        return {
            "src": obj.src.url if obj.src else None,
            "alt": obj.alt
        }

    def get_subcategories(self, obj: Category):
        subcategories = obj.subcategories.all()
        return CategorySerializer(subcategories, many=True).data


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders"""
    products = serializers.SerializerMethodField()
    fullName = serializers.CharField(source='profile.fullName', read_only=True)
    phone = serializers.CharField(source='profile.phone', read_only=True)
    email = serializers.CharField(source='profile.email', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'createdAt',
            'fullName',
            'email',
            'phone',
            'deliveryType',
            'paymentType',
            'totalCost',
            'status',
            'city',
            'address',
            'products'
        )

    def get_products(self, obj: Order):
        order_items = OrderItem.objects.filter(order=obj)
        products = [item.product for item in order_items]
        return CatalogProductSerializer(products, many=True).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        date_format = '%Y-%m-%d %H:%M'
        representation['createdAt'] = instance.createdAt.strftime(date_format)
        return representation


class OrderConfirmSerializer(OrderSerializer):
    """Serializer for order confirmation"""
    def validate(self, data):
        delivery_type = data['deliveryType']
        try:
            delivery_payment_parameters = OrderDeliveryType.objects.get(type=delivery_type)
        except OrderDeliveryType.DoesNotExist:
            raise serializers.ValidationError(f"Unsupported delivery type: {data['deliveryType']}")

        if delivery_type == 'free' and data['totalCost'] > delivery_payment_parameters.min_cost:
            return data

        data['totalCost'] = data['totalCost'] + delivery_payment_parameters.delivery_cost
        return data


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payments"""
    class Meta:
        model = Payment
        fields = ('number', 'name', 'year', 'month', 'code')

    def validate_year(self, value: str):
        if not value.isdigit() or len(value) != 4:
            raise serializers.ValidationError("Expiry year must be a 4-digit number.")
        return value

    def validate_month(self, value: str):
        if not value.isdigit() or not (1 <= int(value) <= 12):
            raise serializers.ValidationError("Expiry month must be a number between 01 and 12.")
        return value

    def validate_code(self, value: str):
        if not value.isdigit() or not (3 <= len(value) <= 4):
            raise serializers.ValidationError("CVV must be a 3 or 4-digit number.")
        return value

    def create(self, validated_data):
        order = self.context['order']
        payment = Payment.objects.create(order=order, **validated_data)
        return payment


class SaleProductsSerializer(serializers.ModelSerializer):
    """Serializer for sale products"""
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'price', 'title', 'images')


class SaleSerializer(serializers.ModelSerializer):
    """Serializer for sales"""
    product = SaleProductsSerializer(read_only=True)

    class Meta:
        model = Sale
        fields = ('product', 'salePrice', 'dateFrom', 'dateTo')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        product_data = representation.pop('product')
        for key, value in product_data.items():
            representation[key] = value
        date_format = '%m-%d'
        representation['dateFrom'] = instance.dateFrom.strftime(date_format)
        representation['dateTo'] = instance.dateTo.strftime(date_format)
        return representation
