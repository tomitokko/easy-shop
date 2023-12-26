from django.shortcuts import render, redirect 
from django.contrib.auth.models import User, auth
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.views.generic import View
from django.contrib.auth.decorators import login_required
import random
import uuid
from datetime import datetime
import hashlib
import re
import json
import ast
from django.http import JsonResponse
from collections import defaultdict
from .models import Wishlist, Product, Order
from dateutil import parser
from django.contrib import messages


# this function check if a user already has a store
def has_store(username):
    with connection.cursor() as cursor:
        # Check if the user already has a store
        cursor.execute("SELECT id FROM shop_store WHERE owner_username = %s", [username])
        result = cursor.fetchone()
        if result is None:
            return False
        else: 
            return True

category_list = [
    "electronics",
    "clothing",
    "kitchen utensils",
    "Automotive Parts & Accessories",
    "Groceries",
    "Home & Kitchen",
    "Beauty & Personal Care",
    "Cleaning supplies",
    "Gifts"
]


# this returns the id of the store of the current user
def get_store_id(username):
    with connection.cursor() as cursor:
        sql_query = """
            SELECT id
            FROM shop_store
            WHERE owner_username = %s
        """
        cursor.execute(sql_query, [username])
        result = cursor.fetchone()
        if result:
            store_id = result[0]
        else:
            store_id = None
        return store_id


def index(request):
    # Connect to the database
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM shop_product")
    products = cursor.fetchall()
    # truncate list of products to first 3
    products = products[:3]


    # Get the current user's username
    username = request.user.username

    # Get the user's most recent product views
    cursor = connection.cursor()
    cursor.execute("""
        SELECT product_id 
        FROM shop_productview 
        WHERE user_username = %s 
        ORDER BY timestamp DESC 
        LIMIT 3
    """, [username])
    most_recent_product_ids = [row[0] for row in cursor.fetchall()]

    # Get the products that match the user's most recently viewed products' categories
    most_recent_product_category_products = []
    for product_id in most_recent_product_ids:
        cursor.execute("""
            SELECT * 
            FROM shop_product 
            WHERE category = (
                SELECT category 
                FROM shop_product 
                WHERE id = %s
            ) 
            LIMIT 3
        """, [product_id])
        products_suggestion = cursor.fetchall()
        most_recent_product_category_products.extend(products_suggestion)

    # Get the products that match the user's most recent search terms
    cursor.execute("""
        SELECT term 
        FROM shop_search 
        WHERE user_username = %s 
        ORDER BY date_created DESC 
        LIMIT 3
    """, [username])
    most_recent_search_terms = [row[0] for row in cursor.fetchall()]
    
    
    most_recent_search_term_products = []
    for search_term in most_recent_search_terms:
        cursor.execute("""
            SELECT * 
            FROM shop_product 
            WHERE name LIKE %s OR category LIKE (
                SELECT category
                FROM shop_product
                WHERE name LIKE %s
            ) 
            LIMIT 3
        """, ['%'+search_term+'%', '%'+search_term+'%'])
        search_results = cursor.fetchall()
        most_recent_search_term_products.extend(search_results)

    # Get the products that the user has ordered before
    cursor.execute("""
        SELECT product_id 
        FROM shop_cart 
        WHERE user_username = %s AND bought = TRUE
    """, [username])
    # Retrieving the product IDs of the products that the current user has ordered before from the shop_cart table
    ordered_product_ids = [row[0] for row in cursor.fetchall()]

    # Get the products that are similar to the ones the user has purchased before
    similar_ordered_products = []
    for product_id in ordered_product_ids:
        cursor.execute("""
            SELECT * 
            FROM shop_product 
            WHERE category = (
                SELECT category 
                FROM shop_product 
                WHERE id = %s
            ) 
            LIMIT 3
        """, [product_id])
        products_suggestion = cursor.fetchall()
        similar_ordered_products.extend(products_suggestion)


    # Retrieving the user's store ID using the get_store_id function
    users_store_id = get_store_id(username)
    
    # Creating a dictionary of context variables to be passed to the index.html template
    context = {
        'category_list': category_list,
        'has_store': has_store(username),
        'most_recent_viewed_recommendations': most_recent_product_category_products,
        'most_recent_searches_recommendations': most_recent_search_term_products,
        'similar_ordered_products': similar_ordered_products,
        'products': products,
        'users_store_id': users_store_id,
    }
    return render(request, 'index.html', context)



@login_required
def wishlist(request):
    # Get the current user's username
    username = request.user.username

    # Use the get_wishlist_products method to get all the products in the wishlist
    wishlist_products = Wishlist.get_wishlist_products(username)


    # Set up the context dictionary with the wishlist products to pass to the template
    context = {
        'products': wishlist_products,
    }

    # Render the wishlist.html template with the wishlist products as the context
    return render(request, 'wishlist.html', context)



class AddToWishlistView(View):
    def get(self, request, product_id):
        # Get the current user's username
        username = request.user.username
        
        # Check if the product is already in the user's wishlist
        cursor = connection.cursor()
        query = """
            SELECT COUNT(*) 
            FROM shop_wishlist 
            WHERE user_username = %s AND product_id = %s
        """
        cursor.execute(query, [username, product_id])
        count = cursor.fetchone()[0]

        # If the product is already in the user's wishlist, redirect back to the product page with an error message
        if count > 0:
            # Set the error message in the session
            request.session['wishlist_error'] = 'This item is already in your wishlist'
            return redirect('product', pk=product_id)
        else:
            # If the product is not already in the user's wishlist, add it to the wishlist
            Wishlist.add_to_wishlist(username, product_id)
        
        # Redirect back to the product page
        return redirect('product', pk=product_id)
    


@login_required
def remove_from_wishlist(request, product_id):
    # Get the current user's username
    username = request.user.username

    if Wishlist.objects.filter(user_username=username, product_id=product_id):
        # Get the wishlist item to remove
        wishlist_item = Wishlist.objects.get(user_username=username, product_id=product_id)
    

        # Remove the item from the user's wishlist
        wishlist_item.remove_from_wishlist()

        # Redirect back to the product page
        return redirect('product', pk=product_id)

    else:
        # Set the error message in the session
        request.session['wishlist_error'] = 'This item is not in your wishlist'
        return redirect('product', pk=product_id)


def category_view(request, category):
    query = """
        SELECT * 
        FROM shop_product
        WHERE category = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [category])
        products = cursor.fetchall()

    context = {
        'category': category,
        'count': len(products),
        'products': products,
        'category_list': category_list,
    }

    return render(request, 'categories.html', context)


@login_required
def create_store(request):
    # check to see if the current user already has a store
    
    def hashing(code):
        # create a new sha256 hash object
        hash_object = hashlib.sha256()

        # update the hash object with the bytes of the code
        hash_object.update(code.encode())

        # get the hexadecimal representation of the hash
        hashed_code = hash_object.hexdigest()

        # returns the hashed code
        return(hashed_code)

    def check_hash(hashed_code, check_code):

        # create a new sha256 hash object
        check_hash_object = hashlib.sha256()

        # update the hash object with the bytes of the code
        check_hash_object.update(check_code.encode())

        # get the hexadecimal representation of the hash
        check_hashed_code = check_hash_object.hexdigest()

        # compare the hashed codes
        if hashed_code == check_hashed_code:
            return True
        else:
            return False

    def create_new_store(name, description, owner_username, passcode, date_created):
        id = str(uuid.uuid4())
        
        date_created = date_created()
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO shop_store (id, name, description, owner_username, passcode, date_created, amount_of_orders, amount_of_products) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", [id, name, description, owner_username, passcode, str(date_created), 0, 0])
    
    if request.method == 'POST':
        store_name = str(request.POST['store_name'])
        store_description = str(request.POST['store_description'])
        store_passcode = str(request.POST['store_passcode'])
        current_user = request.user.username
        store_owner_username = str(current_user)
        date_created = datetime.now

        # hash 6-digit code
        hashed_store_passcode = hashing(store_passcode)

        if store_name != "" and store_description != "": 
            # check if store name is already taken
            query = 'SELECT name FROM shop_store WHERE name = %s'
            with connection.cursor() as cursor:
                cursor.execute(query, [store_name])
                row = cursor.fetchone()
            if row is None:
                # create a new store by calling the create_store function
                create_new_store(store_name, store_description, store_owner_username, hashed_store_passcode, date_created)
                return redirect('/')
            else:
                # return an error saying name already taken
                return render(request, 'create.html', {'error': 'Sorry, the store name is already taken'})
            
            
        else:
            return render(request, 'create.html', {'error': 'Please fill in all required information'})


    return render(request, 'create.html')

@login_required
def add_product(request):
    # Check if the current user has a store
    if has_store(request.user.username) == True:
        # Define a helper function to create a new product
        def create_new_product(name, description, owner_username, store_id, first_image, second_image, third_image, price, category):
            # Generate a new UUID for the product ID
            id = str(uuid.uuid4())
            
            # Get the current date and time
            date_created = datetime.now()
            
            # Insert the new product into the database
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO shop_product (id, name, description, owner_username, store_id, first_image, second_image, third_image, price, category, date_created, amount_of_orders) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                [id, name, description, owner_username, store_id, first_image, second_image, third_image, price, category, str(date_created), 0])
        
        if request.method == 'POST':
            # Get the product information from the POST data
            product_name = str(request.POST['product_name'])
            product_description = str(request.POST['product_description'])
            
            # Save the uploaded images and get their references
            first_image_reference = request.FILES.get('first_image')
            first_image = default_storage.save(first_image_reference.name, first_image_reference)
            second_image_reference = request.FILES.get('second_image')
            second_image = default_storage.save(second_image_reference.name, second_image_reference)
            third_image_reference = request.FILES.get('third_image')
            third_image = default_storage.save(third_image_reference.name, third_image_reference)
            
            # Get the product price and category
            price = request.POST['price']
            product_category = str(request.POST['product_category'])
            
            # Get the current user's username and store ID
            owner_username = request.user.username
            store_id = get_store_id(request.user.username)
            
            # Create the new product
            create_new_product(product_name, product_description, owner_username, store_id, first_image, second_image, third_image, price, product_category)

        # Render the 'add-product.html' template with the 'has_store' context variable
        context = {
            'has_store': has_store(request.user.username)
        }
        return render(request, 'add-product.html', context)
    
    # If the current user does not have a store, redirect to the home page
    else:
        return redirect('/')

@login_required
def edit_product(request, product_id):
    # Check if the current user has a store
    if not has_store(request.user.username):
        return redirect('/')

    # Retrieve the product to edit
    product = Product.objects.get(pk=product_id)

    # Check if the product belongs to the current user
    if product.owner_username != request.user.username:
        return redirect('/')

    # Create a new cursor to interact with the database
    cursor = connection.cursor()
        
    # Update the product
    if request.method == 'POST':
        # Get the data from the form
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description')
        first_image_reference = request.FILES.get('first_image')
        second_image_reference = request.FILES.get('second_image')
        third_image_reference = request.FILES.get('third_image')
        price = request.POST.get('price')
        product_category = request.POST.get('product_category')

        # If a new first image was provided, save it
        if first_image_reference:
            first_image = default_storage.save(first_image_reference.name, first_image_reference)
        else:
            # If no first image was provided, retrieve the existing first image from the database
            cursor.execute("SELECT first_image FROM shop_product WHERE id = %s", [product_id])
            first_image = cursor.fetchone()[0]

        # If a new second image was provided, save it
        if second_image_reference:
            second_image = default_storage.save(second_image_reference.name, second_image_reference)
        else:
            # If no second image was provided, retrieve the existing second image from the database
            cursor.execute("SELECT second_image FROM shop_product WHERE id = %s", [product_id])
            second_image = cursor.fetchone()[0]

        # If a new third image was provided, save it
        if third_image_reference:
            third_image = default_storage.save(third_image_reference.name, third_image_reference)
        else:
            # If no third image was provided, retrieve the existing third image from the database
            cursor.execute("SELECT third_image FROM shop_product WHERE id = %s", [product_id])
            third_image = cursor.fetchone()[0]

        # Update the product in the database
        with connection.cursor() as cursor:
            query = """
                UPDATE shop_product 
                SET name=%s, description=%s, first_image=%s, second_image=%s, third_image=%s, 
                price=%s, category=%s 
                WHERE id=%s
            """
            cursor.execute(query, [product_name, product_description, first_image, second_image, third_image, price, product_category, product_id])

        # Redirect to the product page
        return redirect('product', pk=product_id)

    # Set up the context for rendering the template
    context = {
        'product': product,
        'has_store': True,
    }
    return render(request, 'edit-product.html', context)



@login_required
def delete_product(request):
    def check_hash(hashed_code, check_code):

        # create a new sha256 hash object
        check_hash_object = hashlib.sha256()

        # update the hash object with the bytes of the code
        check_hash_object.update(check_code.encode())

        # get the hexadecimal representation of the hash
        check_hashed_code = check_hash_object.hexdigest()

        # compare the hashed codes
        if hashed_code == check_hashed_code:
            return True
        else:
            return False
        
    if request.method == "POST":
        username = request.user.username
        product_id = request.POST['product_id']
        store_passcode = request.POST['store_passcode']
        print('hiiii')
        print(product_id)
        print(store_passcode)
        # Check if the product is owned by the current user
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id 
                FROM shop_product 
                WHERE owner_username = %s AND id = %s
            """, [username, product_id])
            product = cursor.fetchone()

        # If the product is owned by the user, delete it
        if product:
            # get the passcode of the store in hashed format
            with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT passcode FROM shop_store
                        WHERE owner_username = %s
                    """, [username])
                    hashed_store_passcode = cursor.fetchone()[0]

            # check if the passcode inputted is correct
            passcode_check = check_hash(hashed_store_passcode, store_passcode)
            if passcode_check is True:
                # delete the product
                with connection.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM shop_product 
                        WHERE id = %s
                    """, [product_id])

                return redirect('/')
            else:
                messages.error(request, "Store Passcode Incorrect")
                return redirect(f'/product/{product_id}')
        else:
            return HttpResponse("You do not have permission to delete this product.")
    
    else:
        redirect('/')


@login_required
def store_dashboard(request):

    cursor = connection.cursor()

    store_sql = """
        SELECT *
        FROM shop_store
        WHERE owner_username = %s
    """
    cursor.execute(store_sql, [request.user.username])
    store_details = cursor.fetchone()

    orders_sql = """
        SELECT date_ordered 
        FROM shop_order 
        WHERE store_id = (
            SELECT id 
            FROM shop_store 
            WHERE owner_username = %s
        )
    """
    cursor.execute(orders_sql, [request.user.username])
    all_orders = cursor.fetchall()
    

    order_dictionary = defaultdict(int)
    for item in all_orders:
        order_dictionary[item[0]] += 1

    order_dictionary = dict(order_dictionary)

    order_dictionary = {str(k): v for k, v in order_dictionary.items()}

    new_order_dictionary = {}
    for key, value in order_dictionary.items():
        date = parser.parse(key)
        date_string = date.strftime("%Y-%m-%d")
        if date_string in new_order_dictionary:
            new_order_dictionary[date_string] += value
        else:
            new_order_dictionary[date_string] = value

    new_order_dictionary = json.dumps(new_order_dictionary)




    # store_id = get_store_id(request.user.username)

    """
    The SQL query below retrieves the names of all products of the currently logged 
    in store owner and the total number of times each product has been ordered, taking
    into account that a product can be ordered multiple times in different carts
    """
    query = """
        SELECT p.name, SUM(c.quantity) AS total_quantity_ordered, p.id
        FROM shop_product p
        INNER JOIN shop_store s ON p.store_id = s.id
        INNER JOIN shop_cart c ON p.id = c.product_id AND s.id = c.store_id
        INNER JOIN shop_order o ON c.id = o.cart_detail_id
        WHERE s.owner_username = %s
        GROUP BY p.name, p.id
        ORDER BY total_quantity_ordered DESC
        LIMIT 5
    """

    cursor = connection.cursor()
    cursor.execute(query, [request.user.username])
    product_order_details = cursor.fetchall()
    
    product_order_details_label = []
    product_order_details_data = []
    for product in product_order_details:
        product_order_details_label.append(product[0])
        product_order_details_data.append(product[1])


    if product_order_details:
        # Get the details of the most bought product
        get_query = """
            SELECT * FROM shop_product WHERE id = %s
        """
        cursor = connection.cursor()
        cursor.execute(get_query, [product_order_details[0][2]])
        most_bought_product = cursor.fetchone()
    else:
        most_bought_product = ()
    
    


    # Use a raw SQL query to get the total amount of money the store has made based on sales
    total_money_query = """
        SELECT SUM(cart.quantity * product.price)
        FROM shop_cart AS cart
        JOIN shop_product AS product ON cart.product_id = product.id
        JOIN shop_order AS o ON cart.id = o.cart_detail_id
        WHERE o.store_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(total_money_query, [get_store_id(request.user.username)])
        total_sales = cursor.fetchone()[0]

    # Use Django's ORM to get the amount of orders the store has received
    orders_count = Order.objects.filter(store_id=get_store_id(request.user.username)).count()


    # Render the store-dashboard.html template with all the necessary information as context

    context = {
        'store_details': store_details,
        'order_dictionary': new_order_dictionary,
        'product_order_details': product_order_details,
        'product_order_details_label': product_order_details_label,
        'product_order_details_data': product_order_details_data,
        'most_bought_product': most_bought_product,
        'total_sales': total_sales,
        'orders_count': orders_count
    }
    return render(request, 'store-dashboard.html', context)


def store(request, pk):
    # get the store id from the URL parameter
    store_id = pk

    # retrieve the details of the store using the store id
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM shop_store WHERE id = %s", [store_id])
    store_details = cursor.fetchone()

    # retrieve all the products in the store using the store id
    cursor.execute("SELECT * FROM shop_product WHERE store_id = %s", [store_id])
    products = cursor.fetchall()

    # retrieve the email of the store owner using the store id
    query = """
            SELECT email 
            FROM auth_user 
            WHERE username = (
                SELECT owner_username
                FROM shop_store
                WHERE id = %s
            )
            """
    cursor.execute(query, [store_id])
    owners_email = cursor.fetchone()[0]

    # create a context dictionary with the store details, products, and owner's email
    context = {
        'store_details': store_details,
        'products': products,
        'owners_email': owners_email,
    }

    # render the store.html template with the context dictionary as context
    return render(request, 'store.html', context)

def product(request, pk):
    product_id = pk
    user_username = request.user.username

    # get the details of current product
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM shop_product WHERE id = %s", [product_id])
    product_details = cursor.fetchone()

    # get id of the store that owns that product
    cursor.execute("SELECT store_id FROM shop_product WHERE id = %s", [product_id])
    product_store_id = cursor.fetchone()

    # get the name of the store that owns the product
    cursor.execute("SELECT name FROM shop_store WHERE id = %s", [product_store_id[0]])
    store_name = cursor.fetchone()[0]

    # get list of suggested products
    cursor.execute("SELECT * FROM shop_product WHERE category = %s", [product_details[9]])
    similar_products = cursor.fetchall()

    # using list comprehension to iterate over the list of similar products and remove the current product from similar product
    target_id = product_id
    filtered_similar_products = [x for x in similar_products if target_id not in x]


    # add to product view database
    cursor.execute("INSERT INTO shop_productview (id, product_id, user_username, timestamp) VALUES (%s, %s, %s, %s)", [str(uuid.uuid4()), product_id, request.user.username, str(datetime.now())])


    # Check if the product is in the user's wishlist
    query = """
        SELECT COUNT(*) 
        FROM shop_wishlist 
        WHERE user_username = %s AND product_id = %s
    """
    cursor.execute(query, [user_username, product_id])
    count = cursor.fetchone()[0]

    if count > 0:
        wishlist_check = True
    else:
        wishlist_check = False


    # get the value of a wishlist error if sent to the product view
    wishlist_error = request.session.pop('wishlist_error', None)
    

    # check if a the current product is owned by the currently logged in user
    check_query = """
        SELECT COUNT(*) 
        FROM shop_product 
        WHERE id = %s AND owner_username = %s
    """

    cursor.execute(check_query, [product_id, user_username])

    # Get the result of the query
    product_count = cursor.fetchone()[0]

    # Return True if the product is owned by the user, False otherwise
    if product_count > 0:
        owned_by_logged_in_user = True
    else:
        owned_by_logged_in_user = False

    context = {
        'product_details': product_details,
        'product_store_id': product_store_id,
        'store_name': store_name,
        'similar_products': filtered_similar_products,
        'wishlist_check': wishlist_check,
        'wishlist_error': wishlist_error,
        'owned_by_logged_in_user': owned_by_logged_in_user,
    }
    return render(request, 'product.html', context)


def search(request):
    # Check if the search form has been submitted
    if request.method == 'POST':
        # Retrieve the search term from the form
        search_term = request.POST.get('search_term')

        # Clean up the search term by removing leading/trailing spaces and non-alphanumeric characters
        search_term = search_term.strip()
        search_term = re.sub(r'[^\w\s]', '', search_term)

        # Get the current date and time
        date_created = datetime.now()

        # Define SQL query for retrieving products matching the search term
        query = """
            SELECT *
            FROM shop_product
            WHERE name LIKE %s OR description LIKE %s
        """

        # Execute the query with search_term as parameter
        with connection.cursor() as cursor:
            cursor.execute(query, [f'%{search_term}%', f'%{search_term}%'])
            products = cursor.fetchall()

            # Insert search term and date into shop_search table
            cursor.execute("INSERT INTO shop_search (id, term, user_username, date_created) VALUES (%s, %s, %s, %s)",
                [str(uuid.uuid4()), search_term, request.user.username, str(date_created)])

        # Render the search.html template with the retrieved products as context
        return render(request, 'search.html', {'products': products})

    # Render the search.html template if the search form has not been submitted yet
    return render(request, 'search.html')



@login_required
def cart(request):
    # Get the username of the current user
    current_user = request.user.username

    # Use parameterized queries to separate SQL code from user input
    cursor = connection.cursor()

    # Use SQL aggregation functions to calculate the total quantity and price of all items in the cart
    sql_query = """
        SELECT SUM(sc.quantity), SUM(sp.price * sc.quantity)
        FROM shop_cart sc 
        INNER JOIN shop_product sp ON sc.product_id = sp.id 
        WHERE sc.user_username = %s AND sc.bought = False
    """
    cursor.execute(sql_query, [current_user])
    cart_totals = cursor.fetchone()

    # Extract the total quantity and price from the query result
    total_items_quantity = cart_totals[0] or 0
    total_price = cart_totals[1] or 0

    # Use parameterized queries to join the shop_cart and shop_product tables
    sql_query = """
        SELECT sp.name, sp.price, sp.id, sc.quantity 
        FROM shop_cart sc 
        INNER JOIN shop_product sp ON sc.product_id = sp.id 
        WHERE sc.user_username = %s AND sc.bought = False
    """
    cursor.execute(sql_query, [current_user])
    user_cart = cursor.fetchall()

    # Create a context dictionary with the products details and cart totals
    context = {
        'products_details': user_cart,
        'total_items_quantity': total_items_quantity,
        'total_price': total_price,
    }
    
    # Render the cart.html template with the context dictionary
    return render(request, 'cart.html', context)



@login_required
def checkout(request):
    # Get the username of the current user
    current_user = request.user.username

    # Create a cursor object to execute SQL queries
    cursor = connection.cursor()

    # Define SQL query to fetch the user's address from the shop_address table
    address_query = """
        SELECT *
        FROM shop_address
        WHERE user_username = %s
    """

    # Execute the query with the current user's username as parameter
    cursor.execute(address_query, [request.user.username])

    # Fetch the user's address from the query result
    user_address = cursor.fetchone()

    # Define SQL query to fetch the user's cart items from the shop_cart table
    cart_query = """
        SELECT *
        FROM shop_cart
        WHERE user_username = %s AND bought = False
    """

    # Execute the query with the current user's username as parameter
    cursor.execute(cart_query, [current_user])

    # Fetch all the user's cart items from the query result
    user_cart = cursor.fetchall()

    # Initialize an empty list to store the details of each cart item
    products_details = []

    # Loop over each cart item and retrieve its details from the shop_product table
    for product in user_cart:
        # Define SQL query to fetch the details of the product with the corresponding ID from the shop_product table
        product_query = """
            SELECT name, price, id 
            FROM shop_product 
            WHERE id = %s
        """
        # Execute the query with the product's ID as parameter
        cursor.execute(product_query, [product[1]])

        # Fetch the details of the product from the query result
        row = cursor.fetchone()

        # If the query result is not None, add the product details, along with the cart quantity and ID, to the list of products_details
        if row is not None:
            products_details.append(list(row+(product[3], product[0], product[5])))

    # Initialize variables to calculate the total number of items and price in the cart
    total_items_quantity = 0
    total_price = 0

    # Loop over each product in the cart and update the total quantity and price
    for product in products_details:
        total_items_quantity += product[3]
        total_price += product[1] * product[3]

    # Create a context dictionary with the product details, total quantity and price, and user's address
    context = {
        'products_details': products_details,
        'total_items_quantity': total_items_quantity,
        'total_price': total_price,
        'user_address': user_address
    }

    # Render the checkout.html template with the context dictionary
    return render(request, 'checkout.html', context)



@login_required
def add_to_cart(request):
    # Check if the request method is POST
    if request.method == 'POST':
        # Generate a unique ID for the cart item
        cart_id = uuid.uuid4()
        # Get the product ID, store ID, quantity, and user's username from the request POST data
        product_id = request.POST['product_id']
        store_id = request.POST['store_id']
        quantity = request.POST['quantity']
        user_username = request.user.username

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        # Define SQL query to insert the cart item into the shop_cart table
        cart_query = """
            INSERT INTO shop_cart 
            (id, product_id, store_id, user_username, quantity, bought) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        # Execute the query with the cart item details as parameters
        cursor.execute(cart_query, [str(cart_id), product_id, store_id, user_username, quantity, False])

        # Redirect the user to the product page
        return redirect('/product/'+product_id)
    else:
        # If the request method is not POST, redirect the user to the homepage
        return redirect('/')



@login_required
def update_cart_product(request):
    if request.method == 'POST':
        product_id = request.POST['product_id']
        quantity = request.POST['quantity']
        cursor = connection.cursor()

        # Use parameterized query to retrieve the cart owner
        sql_query = """
            SELECT user_username FROM shop_cart WHERE product_id = %s
        """
        cursor.execute(sql_query, [product_id])
        cart_owner = cursor.fetchone()[0]

        # Check if the user trying to update the cart is the owner of the cart (this is done for security purposes)
        if cart_owner == request.user.username:
            # Use parameterized query to update the cart
            sql_query = """
                UPDATE shop_cart SET quantity = %s WHERE product_id = %s
            """
            cursor.execute(sql_query, [quantity, product_id])
            return redirect('/cart')
        else:
            return redirect('/')
    else:
        return redirect('/')



@login_required
def payment_complete(request):
    
    products_bought = []
    total_amount = 0
    # create an order
    for order in ast.literal_eval(request.POST['products_details']):
        order_id = uuid.uuid4()
        user_username = request.user.username
        cart_detail_id = order[4]
        cart_store_id = order[5]
        status = 'P'

        cursor = connection.cursor()
        # sql query to create an order
        cursor.execute("INSERT INTO shop_order (id, user_username, cart_detail_id, date_ordered, store_id, status) VALUES (%s, %s, %s, %s, %s, %s)", [str(order_id), user_username, cart_detail_id, str(datetime.now()), cart_store_id, status])

        
        # clear cart by setting bought as True
        cursor.execute("UPDATE shop_cart SET bought = True WHERE id = %s", [cart_detail_id])

        # get details of all product bought

        # Define the parameterized SQL query to get the details of products bought
        query = """
            SELECT c.product_id, c.quantity, p.name, p.price, SUM(c.quantity * p.price) as amount
            FROM shop_cart c
            JOIN shop_product p ON c.product_id = p.id
            WHERE c.id = %s
            GROUP BY c.product_id, c.quantity, p.name, p.price
        """

        # Execute the query with the cart_detail_id parameter
        cursor.execute(query, [cart_detail_id])

        # Fetch the results and process them as before
        cart_details = cursor.fetchall()
        
        for cart in cart_details:
            product_id, quantity, name, price, amount = cart
            products_bought.append((product_id, quantity, name, price, amount))

        # calculate the total amount the spent in purchasing products
        total_amount = total_amount + sum([cart[4] for cart in cart_details])
    

    # Store data in session
    request.session['invoice_data'] = products_bought
    request.session['total_amount'] = total_amount

    # Redirect the user to the invoice page
    return redirect('/invoice')



def invoice(request):
    username = request.user.username

    # get address of the logged in user
    address_query = """
        SELECT *
        FROM shop_address
        WHERE user_username = %s
    """

    cursor = connection.cursor()
    cursor.execute(address_query, [username])
    # Fetch the user's address
    user_address = cursor.fetchone()

    # Get data from session
    invoice_data = request.session.get('invoice_data')
    total_amount = request.session.get('total_amount')

    # check if the invoice data has been successfulyy retrieved from the session
    if invoice_data and total_amount:

        # add the data to the context dictionary
        context = {
            'invoice_data' : invoice_data,
            'total_amount' : total_amount,
            'user_address' : user_address,
        }
    
    else:
        # make the context dictionary empty if the invoice data hasn't been successfully retrieved
        context = {}

    # Clear data from session to avoid reusing it
    request.session.pop('invoice_data', None)
    request.session.pop('total_amount', None)

    return render(request, 'invoice.html', context)


@login_required
def account(request):
    username = request.user.username

    # Check if the user already has an address
    query = "SELECT * FROM shop_address WHERE user_username = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, [username])
        address = cursor.fetchone()
    
    # If the user has an address, prepopulate the form with their existing address data
    if address:
        initial_address = {'street_address': address[2], 'city': address[3], 'post_code': address[5], 'country': address[4]}
    # If the user doesn't have an address, create a new form with no initial data
    else:
        initial_address = {}
    
    # Render the form with the appropriate initial data
    return render(request, 'account.html', {'initial_address': initial_address})


@login_required
def create_or_update_address(request):
    username = request.user.username
    
    if request.method == 'POST':
        # Get the form data from the request object
        street = request.POST.get('street')
        city = request.POST.get('city')
        post_code = request.POST.get('post_code')
        country = request.POST.get('country')
        
        # Construct the SQL query as a parameterized string
        # This SQL query inserts or updates an address in the shop_address table for a user. The query uses a the ON CONFLICT clause to update the address if it already exists, using the user_username as the conflict resolution parameter.
        query = """
            INSERT INTO shop_address (id, user_username, street, city, post_code, country)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_username) DO UPDATE
            SET street = %s, city = %s, post_code = %s, country = %s
            """
        
        # Execute the SQL query with the form data as parameters
        with connection.cursor() as cursor:
            cursor.execute(query, [str(uuid.uuid4()), username, street, city, post_code, country,
                                   street, city, post_code, country])
        
        # Redirect the user to a success page
        return redirect('account')
    
    else:
       return redirect('/account')


@login_required
def update_profile_details(request):
    user_id = request.user.id
    
    if request.method == 'POST':
       # Get the form data from the request object
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Construct the SQL query as a parameterized string
        query = """
            UPDATE auth_user
            SET first_name = %s, last_name = %s
            WHERE id = %s
            """
        
        # Get the current user ID
        user_id = request.user.id
        
        # Execute the SQL query with the form data as parameters
        with connection.cursor() as cursor:
            cursor.execute(query, [str(first_name), str(last_name), user_id])
        
        
        # Redirect the user to a success page
        return redirect('/account')
    
    else:
        # Render the profile update form
        return redirect('/account')


@login_required
def orders(request):
    # Define the SQL query to retrieve the required details of each order
    sql = """
        SELECT o.date_ordered, p.name AS product_name, c.quantity, p.price, o.status, p.id
        FROM shop_order o
        INNER JOIN shop_cart c ON o.cart_detail_id = c.id
        INNER JOIN shop_product p ON c.product_id = p.id
        WHERE o.user_username = %s
    """
    # Get the currently logged-in user's username
    user_username = request.user.username
    # Execute the SQL query with the user's username as a parameter
    with connection.cursor() as cursor:
        cursor.execute(sql, [user_username])
        # Fetch all the results
        results = cursor.fetchall()
    # Convert the results to a list of dictionaries for easier access in the template
    orders = []
    for row in results:
        orders.append({
            'date_ordered': row[0],
            'product_name': row[1],
            'quantity': row[2],
            'price': row[3],
            'status': row[4],
            'product_id': row[5],
        })
    context = {'orders': orders}
    return render(request, 'orders.html', context)



@login_required
def store_dashboard_orders(request):
    # Use a context manager to create a cursor object that will execute the SQL query on the database
    with connection.cursor() as cursor:
        # Execute a SQL query that selects specific columns from multiple tables and joins them together based on certain conditions
        # The query retrieves orders that belong to the store owned by the current user
        # The query returns the order ID, date ordered, quantity, whether the order was bought, product name, product price, store name, order status, product ID, user first name, user last name, user street, user city, user post code, and user country for each order
        # The query uses placeholders and a parameter list to safely insert the current user's username into the query
        cursor.execute("""
            SELECT o.id AS order_id, o.date_ordered, c.quantity, c.bought, p.name AS product_name, p.price, s.name AS store_name, o.status AS status, p.id AS product_id, u.first_name AS first_name, u.last_name AS last_name, a.street AS street, a.city AS city, a.post_code AS post_code, a.country AS country
            FROM shop_order AS o
            JOIN shop_cart AS c ON c.id = o.cart_detail_id
            JOIN shop_product AS p ON p.id = c.product_id
            JOIN shop_store AS s ON s.id = p.store_id
            JOIN auth_user AS u ON u.username = o.user_username
            JOIN shop_address AS a ON a.user_username = u.username
            WHERE s.id = (
                SELECT id
                FROM shop_store
                WHERE owner_username = %s
                LIMIT 1
            )
        """, [request.user.username])
        
        # Fetch all the rows returned by the SQL query
        rows = cursor.fetchall()
        
        # Create an empty list to store the orders
        orders_list = []
        
        # Iterate over each row and append the data to the orders_list as a dictionary
        for row in rows:
            # Unpack the row data into variables
            order_id, date_ordered, quantity, bought, product_name, price, store_name, status, product_id, first_name, last_name, street, city, post_code, country = row
            # Create a dictionary with the row data
            order_dict = {
                'order_id': order_id,
                'date_ordered': date_ordered,
                'quantity': quantity,
                'bought': bought,
                'product_name': product_name,
                'price': price,
                'store_name': store_name,
                'status': status,
                'product_id': product_id,
                'first_name': first_name,
                'last_name': last_name,
                'street': street,
                'city': city,
                'post_code': post_code,
                'country': country,
            }
            # Append the dictionary to the orders_list
            orders_list.append(order_dict)

        # Define the date format to be used for converting datetime objects to strings
        date_format = '%m/%d/%Y'

        # Convert the datetime objects in the orders_list to strings using the specified date format
        for order_dict in orders_list:
            order_dict['date_ordered'] = order_dict['date_ordered'].strftime(date_format)

            # Create a new list that contains the values of each dictionary in the orders_list
            # This is done to convert the list of dictionaries into a list of lists, which is easier to work with in the HTML template
            orders_list = [[order_dict[k] for k in order_dict] for order_dict in orders_list]

            # Render the 'store-dashboard-orders.html' template with the orders_list as a context variable
            return render(request, 'store-dashboard-orders.html', {'orders_list': orders_list})



@login_required
def edit_order(request, order_id):
    # Get the new status from the query parameters in the request
    new_status = request.GET.get('status')

    # Get the current user's username
    current_user = request.user.username

    # Define a SQL query to retrieve the order and store ID for the specified order ID and ensure that the order belongs to the current user's store
    query = """
        SELECT shop_order.*, shop_cart.store_id
        FROM shop_order
        JOIN shop_cart ON shop_order.cart_detail_id = shop_cart.id
        WHERE shop_order.id = %s AND (
            SELECT owner_username
            FROM shop_store
            WHERE id = shop_cart.store_id
        ) = %s
    """

    # Create a cursor object that will execute the SQL query on the database
    with connection.cursor() as cursor:
        # Execute the query using the cursor and the specified parameters
        cursor.execute(query, [order_id, current_user])
        # Fetch the first row returned by the query, or None if there are no rows
        order = cursor.fetchone()

        
        
    # Check if the order belongs to the current user's store; if not, redirect to the order list page
    if order is None:
        return redirect('/store-dashboard/orders')

    # Get the store ID from the order data
    store_id = order[6]

    # Check if the current user owns the store
    query = """
        SELECT *
        FROM shop_store
        WHERE owner_username = %s AND id = %s
    """
    with connection.cursor() as cursor:
        # Execute the query using the cursor and the specified parameters
        cursor.execute(query, [current_user, store_id])
        # Fetch the first row returned by the query, or None if there are no rows
        store = cursor.fetchone()

    # Check if the store is owned by the current user; if not, redirect to the order list page
    if store is None:
        return redirect('/store-dashboard/orders')

    # Define a SQL query to update the status of the specified order ID
    query = """
        UPDATE shop_order
        SET status = %s
        WHERE id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [new_status, order_id])
    
    # Redirect to the order list page after the order status has been updated
    return redirect('/store-dashboard/orders')


def get_cart_count(request):
    
    # create a connection to the database
    cursor = connection.cursor()
    # Using parameterized queries to separate SQL code from user input
    sql_query = "SELECT quantity FROM shop_cart WHERE user_username = %s AND bought = False"
    cursor.execute(sql_query, [request.user.username])

    # Validating user input to ensure it meets expected criteria
    if cursor.rowcount == 0:
        # handle empty result set appropriately
        pass

    # Fetching the result from the execution of the SQL command above
    result = cursor.fetchall()

    # Escaping special characters to prevent SQL injection attacks
    result = [(int(row[0]),) for row in result]


    # function to calculate the sum of all the quantities of the cart and returns the result
    def add_list_of_tuples(lst):
        result = 0
        for i in lst:
            if isinstance(i, tuple):
                for j in i:
                    result += j
            else:
                result += i
        return result

    cart_item_count = add_list_of_tuples(result)

    # returns the cart_item_count as a Json Response
    return JsonResponse({'cart_item_count': cart_item_count})


# The time complexity of the remove_cart_product view function below is O(1), which makes it very efficient
@login_required
def remove_cart_product(request):
    if request.method == 'POST':
        product_id = request.POST['product_id']
        cursor = connection.cursor()

        # Use parameterized query to retrieve the cart owner
        sql_query = """
            SELECT user_username FROM shop_cart WHERE product_id = %s
        """
        cursor.execute(sql_query, [product_id])
        cart_owner = cursor.fetchone()[0]

        # Check if the user trying to remove the cart item is the owner of the cart (this is done for security purposes)
        if cart_owner == request.user.username:
            # Use parameterized query to delete the cart item
            sql_query = """
                DELETE FROM shop_cart WHERE product_id = %s
            """
            cursor.execute(sql_query, [product_id])
            return redirect('/cart')
        else:
            return redirect('/')
    else:
        return redirect('/')



# Define the login view function
def login(request):
    # Check if the request method is POST
    if request.method == 'POST':
        # Retrieve the username and password from the request
        username = request.POST['username']
        password = request.POST['password']

        # Use a context manager and a cursor object to check if the username exists in the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM auth_user WHERE username = %s", [username])
            result = cursor.fetchone()

            # Check if the username is not found in the database, and return an error message
            if result is None:
                return render(request, 'login.html', {'error': 'Invalid Credentials'})
            
            # Perform login operations here
            user = auth.authenticate(username=username, password=password)
                
            # Check if the user is authenticated, and log the user in if successful
            if user is not None:
                auth.login(request, user)
                return redirect('/')
            else:
                return render(request, 'login.html', {'error': 'Credentials Invalid'})
    else:
        # Return the login form to the user
        return render(request, 'login.html')



# The register function is called when the register url is requested
def register(request):

    # Function used to insert a new user into the auth_user table
    def create_user(username, first_name, last_name, email, password):
        # Use the Django database connection object to execute SQL query
        with connection.cursor() as cursor:
            # SQL query to insert new user into auth_user table
            cursor.execute(
                "INSERT INTO auth_user (username, first_name, last_name, email, password, is_superuser, is_staff, is_active, date_joined) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [username, first_name, last_name, email, password, 0, 0, 1, datetime.now()]
            )
    
    # Check that the password is secure
    def check_password_security(username, first_name, last_name, email, password):
        # Check for similarity to username, first name, last name, or email
        if (
            username.lower() in password.lower() or
            first_name.lower() in password.lower() or
            last_name.lower() in password.lower() or
            email.lower() in password.lower()
        ):
            # If the password is too similar, raise a ValidationError
            raise ValidationError("Password is too similar to other personal information.")
        
        # Check that the password is at least 8 characters long
        if len(password) < 8:
            # If the password is too short, raise a ValidationError
            raise ValidationError("Password must be at least 8 characters long.")
    
    if request.method == 'POST':
        # Get values filled in the form on the register page and store them in variables
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        repeat_password = request.POST['repeat_password']

        try:
            # Check that the password is secure
            check_password_security(username, first_name, last_name, email, password)
        except ValidationError as e:
            # Return an error message if the password is not secure
            return render(request, 'register.html', {'error': str(e)})

        # Check if passwords match
        if password == repeat_password:
            # SQL statement to check if username already exists
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM auth_user WHERE username = %s", [username])
                result = cursor.fetchone()
                if result is None:
                    # SQL statement to check if email already exists
                    cursor.execute("SELECT id FROM auth_user WHERE email = %s", [email])
                    email_result = cursor.fetchone()
                    if email_result is None:
                        # Insert the new user into the auth_user table
                        create_user(username, first_name, last_name, email, make_password(password))
                        # Authenticate the new user and log them in
                        user = auth.authenticate(username=username, password=password)
                        auth.login(request, user)
                        # Redirect the user to add an address
                        return redirect('/account')
                    else:
                        # Return an error message if email already exists
                        return render(request, 'register.html', {'error': 'Email already exists'})
                else:
                    # Return an error message if username already exists
                    return render(request, 'register.html', {'error': 'Username already exists'})
        else:
            # Return an error message if passwords do not match
            return render(request, 'register.html', {'error': 'Passwords do not match'})

    # Return the register page if a GET request is received
    return render(request, 'register.html')



# Define the logout view function
def logout(request):
    # Call the logout function from the auth module to log the user out
    auth.logout(request)
    # Redirect the user to the home page
    return redirect('/')
