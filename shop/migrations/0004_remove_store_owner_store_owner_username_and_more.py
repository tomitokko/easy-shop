# Generated by Django 4.1 on 2023-01-13 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_store_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='store',
            name='owner',
        ),
        migrations.AddField(
            model_name='store',
            name='owner_username',
            field=models.CharField(default='tomi', max_length=10000),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='store',
            name='amount_of_orders',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='store',
            name='amount_of_products',
            field=models.IntegerField(default=0),
        ),
    ]
