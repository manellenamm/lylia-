# Generated by Django 3.2.18 on 2023-04-07 12:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('produits', '0005_remove_orderitem_order_information'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='order_information',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='items', to='produits.orderinformation'),
        ),
    ]
