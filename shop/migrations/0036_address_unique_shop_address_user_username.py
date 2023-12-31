# Generated by Django 4.1.7 on 2023-03-05 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0035_remove_address_unique_shop_address_user_username'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='address',
            constraint=models.UniqueConstraint(fields=('user_username',), name='unique_shop_address_user_username'),
        ),
    ]
