# Generated by Django 4.1 on 2023-01-11 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_store_amount_of_products_store_passcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='description',
            field=models.CharField(default='test', max_length=10000),
            preserve_default=False,
        ),
    ]