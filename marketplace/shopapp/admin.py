from django.contrib import admin

from .models import (
    Category, Product, ProductImage,
    Tag, ProductTag, Specification,
    OrderDeliveryType, Sale
)


class ProductImageInline(admin.StackedInline):
    """
    Inline admin descriptor for ProductImage model.
    """
    model = ProductImage


class ProductTagInline(admin.TabularInline):
    """
    Inline admin descriptor for ProductTag model.
    """
    model = ProductTag
    extra = 1


class ProductSpecificationInline(admin.TabularInline):
    """
    Inline admin descriptor for Specification model.
    """
    model = Specification
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin view for Category model.
    """
    list_display = ('title', 'parent')
    search_fields = ('title',)
    verbose_name_plural = 'Categories'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin view for Product model.
    """
    list_display = ('title', 'category', 'price')
    search_fields = ('title',)
    inlines = [
        ProductImageInline,
        ProductTagInline,
        ProductSpecificationInline
    ]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Admin view for Tag model.
    """
    list_display = ('name',)
    search_fields = ('name',)
    verbose_name_plural = 'Tags'


@admin.register(OrderDeliveryType)
class OrderDeliveryTypeAdmin(admin.ModelAdmin):
    """
    Admin view for OrderDeliveryType model.
    """
    model = OrderDeliveryType


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """
    Admin view for Sale model.
    """
    model = Sale

