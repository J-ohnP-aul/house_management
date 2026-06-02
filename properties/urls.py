from django.urls import path
from .views import property_create, property_list, property_detail

urlpatterns = [
    path('create/', property_create, name='property_create'),
    path('p_list', property_list, name='propery_list'),
    path('<slug:slug>', property_detail, name="property_detail")
]