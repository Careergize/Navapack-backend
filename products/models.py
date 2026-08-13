from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    categorySlug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    tag = models.CharField(max_length=255, blank=True)
    imageUrl = models.URLField(blank=True)
    active = models.BooleanField(default=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updatedAt"]

    def __str__(self):
        return self.name
