# Generated manually for the initial Product model.
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("category", models.CharField(max_length=255)),
                ("categorySlug", models.SlugField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("tag", models.CharField(blank=True, max_length=255)),
                ("imageUrl", models.URLField(blank=True)),
                ("active", models.BooleanField(default=True)),
                ("updatedAt", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-updatedAt"]},
        ),
    ]
