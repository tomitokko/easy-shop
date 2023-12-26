from django.db import models
# this is used to generate unique id
import uuid
from datetime import datetime
from django.db import connection


class Store(models.Model):
    id = models.CharField(max_length=1000, primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=10000)
    # foreign key to the user database
    owner_username = models.CharField(max_length=10000)
    date_created = models.DateTimeField(default=datetime.now)
    amount_of_orders = models.IntegerField(default=0)
    amount_of_products = models.IntegerField(default=0)
    passcode = models.CharField(max_length=1000)

    def __str__(self):
        return self.name


class Address(models.Model):
    id = models.CharField(max_length=1000, primary_key=True, default=uuid.uuid4)
    # foreign key to the user database
    user_username = models.CharField(max_length=10000)
    street = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    post_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)


    class Meta:
        # Define a unique constraint on the user_username field
        constraints = [
            models.UniqueConstraint(fields=['user_username'], name='unique_shop_address_user_username')
        ]


class Product(models.Model):
    id = models.CharField(max_length=1000, primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=10000)
    # foreign key to the user database
    owner_username = models.CharField(max_length=10000)
    # foreign key to the store database
    store_id = models.CharField(max_length=1000)
    first_image = models.ImageField(upload_to=f'images/{owner_username}')
    second_image = models.ImageField(upload_to=f'images/{owner_username}')
    third_image = models.ImageField(upload_to=f'images/{owner_username}')
    price = models.IntegerField()
    category = models.CharField(max_length=1000)
    date_created = models.DateTimeField(default=datetime.now)
    amount_of_orders = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Search(models.Model):
    id = models.CharField(max_length=1000, primary_key=True, default=uuid.uuid4)
    term = models.CharField(max_length=10000)
    # foreign key to the user database
    user_username = models.CharField(max_length=10000)
    date_created = models.DateTimeField(default=datetime.now)


    def __str__(self):
        return self.term

class ProductView(models.Model):
    id = models.CharField(max_length=1000, primary_key=True, default=uuid.uuid4)
    # foreign key to link to the product database
    product_id = models.CharField(max_length=10000)
    # foreign key to link to the the user database
    user_username = models.CharField(max_length=10000)
    timestamp = models.DateTimeField(default=datetime.now)


    def __str__(self):
        return self.product_id


class Cart(models.Model):
    id = models.CharField(max_length=1000, primary_key=True, default=uuid.uuid4)
    # foreign key to link to the product database
    product_id = models.CharField(max_length=10000)
    # foreign key to link to the the user database
    user_username = models.CharField(max_length=10000)
    quantity = models.IntegerField(default=1)
    bought = models.BooleanField(default=False)
    # foreign key to link to the store database
    store_id = models.CharField(max_length=10000)

    def __str__(self):
        return self.user_username

class Order(models.Model):
    status_options = (
        ('P', 'Processing'),
        ('S', 'Shipped'),
        ('D', 'Delivered'),
    )
    id = models.CharField(max_length=1000, primary_key=True, default=uuid.uuid4)
    # foreign key to link to the the user database
    user_username = models.CharField(max_length=10000)
    # foreign key to link to the the cart database
    cart_detail_id = models.CharField(max_length=10000)
    # foreign key to link to the store database
    store_id = models.CharField(max_length=10000)
    date_ordered = models.DateTimeField(default=datetime.now)
    status = models.CharField(max_length=1, choices=status_options, default='P')



class Wishlist(models.Model):
    id = models.CharField(max_length=1000, primary_key=True, default=uuid.uuid4)
    # foreign key to link to the the user database
    user_username = models.CharField(max_length=10000)
    # foreign key to link to the product database
    product_id = models.CharField(max_length=10000)
    timestamp = models.DateTimeField(default=datetime.now)


    @staticmethod
    def add_to_wishlist(user_username, product_id):
        query = """
            INSERT INTO shop_wishlist (id, user_username, product_id, timestamp)
            VALUES (%s, %s, %s, %s)
        """

        unique_id = str(uuid.uuid4())

        with connection.cursor() as cursor:
            cursor.execute(query, [unique_id, user_username, product_id, str(datetime.now)])

    @staticmethod
    def remove_from_wishlist(user_username, product_id):
        query = """
            DELETE FROM shop_wishlist 
            WHERE user_username = %s AND product_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [user_username, product_id])

    @staticmethod
    def get_wishlist_products(user_username):
        # Get all the products in the user's wishlist
        query = """
            SELECT * 
            FROM shop_product 
            WHERE id IN (
                SELECT product_id 
                FROM shop_wishlist 
                WHERE user_username = %s
                ORDER BY timestamp DESC
            )
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [user_username])
            products = cursor.fetchall()
        

        return products

    def remove_from_wishlist(self):
        # Delete the wishlist object
        self.delete()