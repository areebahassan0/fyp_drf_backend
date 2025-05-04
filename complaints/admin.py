from django.contrib import admin
from .models import  Category, SubCategory, FurtherSubCategory, Complaint


admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(FurtherSubCategory)
admin.site.register(Complaint)
