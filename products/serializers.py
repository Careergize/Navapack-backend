from rest_framework import serializers
from django.utils.text import slugify
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    categorySlug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = Product
        fields = '__all__'

    def validate(self, attrs):
        # Auto-populate categorySlug from category if missing or blank
        if 'category' in attrs and not attrs.get('categorySlug'):
            attrs['categorySlug'] = slugify(attrs['category'])
        return super().validate(attrs)