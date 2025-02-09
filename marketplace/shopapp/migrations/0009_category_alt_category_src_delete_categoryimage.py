# Generated by Django 5.0.6 on 2024-06-07 11:33

import shopapp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0008_remove_category_image_remove_category_image_alt_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="alt",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="category",
            name="src",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=shopapp.models.category_image_directory_path,
            ),
        ),
        migrations.DeleteModel(
            name="CategoryImage",
        ),
    ]
