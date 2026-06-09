from django.urls import path
from .views import property_create, property_list, property_detail, property_update, unit_create, unit_list, unit_detail

urlpatterns = [
    path('create/', property_create, name='property_create'),
    path('p_list', property_list, name='property_list'),
    path('property/detail/<int:id>/', property_detail, name="property_detail"),
    path('property/update/<int:id>/', property_update, name="property_update"),
    path('unit/create/', unit_create, name='unit_create'),
    path('unit/list/', unit_list, name='unit_list'),
    path('unit/detail/<int:id>/', unit_detail, name='unit_detail'),
]