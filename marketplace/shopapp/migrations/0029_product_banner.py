# Generated by Django 5.0.6 on 2024-06-19 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0028_payment_number_sale"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="banner",
            field=models.BooleanField(default=False),
        ),
    ]
