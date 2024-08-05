from django.urls import path
from .views import CartAPI

app_name = 'cart'

urlpatterns = [
    path("basket", CartAPI.as_view(), name="basket"),
]
