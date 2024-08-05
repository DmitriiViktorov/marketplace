from django.urls import path
from .views import (
    ProductDetailView, CategoryViewSet, CatalogViewSet,
    TagListView, ReviewView, LimitedEditionProductView,
    PopularProductView, OrderView, OrderDetailView,
    PaymentView, SaleView, BannerView,
)

app_name = 'shopapp'

urlpatterns = [
    path("categories/", CategoryViewSet.as_view(), name="category"),
    path("catalog/", CatalogViewSet.as_view(), name="catalog"),
    path("products/popular/", PopularProductView.as_view(), name="popular-products"),
    path("products/limited/", LimitedEditionProductView.as_view(), name="limited-products"),
    path("sales/", SaleView.as_view(), name="sales"),
    path("banners/", BannerView.as_view(), name="banner"),

    path("orders", OrderView.as_view(), name="orders"),
    path("order/<int:pk>", OrderDetailView.as_view(), name="order-details"),

    path("payment/<int:pk>", PaymentView.as_view(), name="payment"),

    path('tags/', TagListView.as_view(), name='tag'),

    path("product/<int:pk>/", ProductDetailView.as_view(), name="product-details"),
    path("product/<int:pk>/reviews", ReviewView.as_view(), name="product-reviews"),
]
