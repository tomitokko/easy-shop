from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Store)
admin.site.register(Address)
admin.site.register(Product)
admin.site.register(Search)
admin.site.register(ProductView)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(Wishlist)