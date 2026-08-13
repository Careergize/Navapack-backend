from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "active", "updatedAt")
    list_filter = ("active", "category")
    search_fields = ("name", "category", "tag")
