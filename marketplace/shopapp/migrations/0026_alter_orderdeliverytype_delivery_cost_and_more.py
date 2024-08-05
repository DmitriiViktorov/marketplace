# Generated by Django 5.0.6 on 2024-06-18 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0025_alter_orderdeliverytype_delivery_cost_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderdeliverytype",
            name="delivery_cost",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.AlterField(
            model_name="orderdeliverytype",
            name="min_cost",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
    ]
