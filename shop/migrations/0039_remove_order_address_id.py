# Generated by Django 4.1.7 on 2023-03-05 20:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0038_order_address_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='address_id',
        ),
    ]
