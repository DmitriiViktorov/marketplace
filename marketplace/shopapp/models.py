import os
from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from myauth.models import Profile


class Product(models.Model):
    """
    Represents a product in the store.

    Attributes:
        title (str): The title of the product.
        count (int): The stock count of the product.
        price (Decimal): The price of the product.
        date (datetime): The date when the product was added.
        description (str, optional): A brief description of the product.
        fullDescription (str, optional): A detailed description of the product.
        freeDelivery (bool): Whether the product has free delivery.
        category (Category, optional): The category of the product.
        sort_index (int): The sorting index of the product.
        limited_edition (bool): Whether the product is a limited edition.
        banner (bool): Whether the product is featured as a banner.
    """
    title = models.CharField(max_length=100)
    count = models.PositiveSmallIntegerField(default=0)
    price = models.DecimalField(
        default=0,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)
    fullDescription = models.TextField(null=True, blank=True)
    freeDelivery = models.BooleanField(default=False)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    sort_index = models.IntegerField(default=0)
    limited_edition = models.BooleanField(default=False)
    banner = models.BooleanField(default=False)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    def clean(self):
        if self.count < 0:
            raise ValidationError('Count cannot be negative.')
        if len(self.title) > 100:
            raise ValidationError('Title cannot exceed 100 characters.')
        if self.price < 0:
            raise ValidationError('Price cannot be negative.')


def product_images_directory_path(instance: "ProductImage", filename: str) -> str:
    """
    Generates the path to upload product images.

    Args:
        instance (ProductImage): The instance of ProductImage.
        filename (str): The original filename of the uploaded image.

    Returns:
        str: The path where the image will be uploaded.
    """
    return "products/product_{pk}/images/{filename}".format(
        pk=instance.product.pk,
        filename=filename,
    )


class ProductImage(models.Model):
    """
    Represents an image for a product.

    Attributes:
        product (Product): The product the image belongs to.
        src (ImageField): The source image file.
        alt (str): The alternative text for the image.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    src = models.ImageField(null=True, blank=True, upload_to=product_images_directory_path)
    alt = models.CharField(null=False, blank=True, max_length=200)

    def save(self, *args, **kwargs):
        if not self.pk:
            super(ProductImage, self).save(*args, **kwargs)

        if self.src and not self.alt:
            self.alt = os.path.splitext(os.path.basename(self.src.name))[0]
            kwargs['force_update'] = True
            super(ProductImage, self).save(*args, **kwargs)


def category_image_directory_path(instance: "Category", filename: str) -> str:
    """
    Generates the path to upload category images.

    Args:
        instance (Category): The instance of Category.
        filename (str): The original filename of the uploaded image.

    Returns:
        str: The path where the image will be uploaded.
    """
    return f"categories/category_{instance.pk}/images/{filename}"


class Category(models.Model):
    """
    Represents a category for products.

    Attributes:
        title (str): The title of the category.
        parent (Category, optional): The parent category if it's a subcategory.
        src (ImageField, optional): The image for the category.
        alt (str): The alternative text for the category image.
    """
    title = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    src = models.ImageField(null=True, blank=True, upload_to=category_image_directory_path)
    alt = models.CharField(null=False, blank=True, max_length=200)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            super(Category, self).save(*args, **kwargs)

        if self.src and not self.alt:
            self.alt = os.path.splitext(os.path.basename(self.src.name))[0]
            kwargs['force_update'] = True
            super(Category, self).save(*args, **kwargs)


class Tag(models.Model):
    """
    Represents a tag for products.

    Attributes:
        name (str): The name of the tag.
    """
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductTag(models.Model):
    """
    Represents the many-to-many relationship between products and tags.

    Attributes:
        product (Product): The related product.
        tag (Tag): The related tag.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('product', 'tag')


class Review(models.Model):
    """
    Represents a review for a product.

    Attributes:
        product (Product): The product being reviewed.
        author (str): The author of the review.
        email (str): The email of the author.
        text (str): The text of the review.
        rate (int): The rating of the product (1-5).
        date (datetime): The date when the review was created.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    author = models.CharField(max_length=100)
    email = models.EmailField()
    text = models.TextField()
    rate = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']


class Specification(models.Model):
    """
    Represents a specification for a product.

    Attributes:
        product (Product): The product the specification belongs to.
        name (str): The name of the specification.
        value (str): The value of the specification.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specifications")
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)


class Order(models.Model):
    """
    Represents a customer's order.

    Attributes:
        profile (Profile, optional): The profile of the customer.
        createdAt (datetime): The date and time when the order was created.
        deliveryType (str): The type of delivery for the order (free, express).
        paymentType (str): The type of payment for the order (online, someone) .
        totalCost (Decimal): The total cost of the order.
        status (str): The current status of the order (accepted, confirmed, paid).
        city (str): The city for the delivery address.
        address (str): The delivery address.
    """
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="orders", null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    deliveryType = models.CharField(max_length=20)
    paymentType = models.CharField(max_length=20)
    totalCost = models.DecimalField(default=0, max_digits=13, decimal_places=2)
    status = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=100)


class OrderItem(models.Model):
    """
    Represents an item in an order.

    Attributes:
        order (Order): The order the item belongs to.
        product (Product): The product being ordered.
        quantity (int): The quantity of the product in the order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=0)


class OrderDeliveryType(models.Model):
    """
    Represents a type of order delivery.

    Attributes:
        type (str): The type of delivery.
        min_cost (Decimal): The cost from which the delivery is free.
        delivery_cost (Decimal): The cost of delivery.
    """
    type = models.CharField(max_length=20)
    min_cost = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    delivery_cost = models.DecimalField(default=0, max_digits=7, decimal_places=2)

    def __str__(self):
        return self.type


class Payment(models.Model):
    """
    Represents a payment for an order.

    Attributes:
        order (Order): The order the payment is for.
        number (str): The card number for the payment.
        name (str): The name on the cardholder.
        year (str): The expiration year of the card.
        month (str): The expiration month of the card.
        code (str): The security code of the card.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    number = models.CharField(max_length=8)
    name = models.CharField(max_length=100)
    year = models.CharField(max_length=4)
    month = models.CharField(max_length=2)
    code = models.CharField(max_length=4)


class Sale(models.Model):
    """
    Represents a sale for a product.

    Attributes:
        product (Product): The product being sold at a discount.
        salePrice (Decimal): The sale price of the product.
        dateFrom (date): The start date of the sale.
        dateTo (date): The end date of the sale.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    salePrice = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    dateFrom = models.DateField()
    dateTo = models.DateField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product.title}: {self.product.price} -> {self.salePrice}"
