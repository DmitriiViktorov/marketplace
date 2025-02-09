# Generated by Django 5.0.6 on 2024-06-06 13:24

import shopapp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0002_alter_product_options_rename_name_product_title_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=shopapp.models.category_image_directory_path,
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="image_alt",
            field=models.CharField(default="No image", max_length=255),
        ),
    ]
