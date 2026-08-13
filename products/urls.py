from django.urls import path

from .views import ProductDetailAPIView, ProductListCreateAPIView

urlpatterns = [
    path("products/", ProductListCreateAPIView.as_view(), name="product-list-create"),
    path("products/<int:pk>/", ProductDetailAPIView.as_view(), name="product-detail"),
]
