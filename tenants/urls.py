from django.urls import path
from . import views

urlpatterns = [
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('tenants/create/', views.tenant_create, name='tenant_create'),
    path('tenants/<int:pk>/update/', views.tenant_update, name='tenant_update'),
    path('tenants/<int:pk>/', views.tenant_detail, name='tenant_detail'),
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/create/', views.reservation_create, name='reservation_create'),
    path('reservations/<int:pk>/update/', views.reservation_update, name='reservation_update'),
    path('reservations/<int:pk>/convert/', views.reservation_convert, name='reservation_convert'),
    path('tenancies/', views.tenancy_list, name='tenancy_list'),
    path('tenancies/create/', views.tenancy_create, name='tenancy_create'),
    path('tenancies/<int:pk>/update/', views.tenancy_update, name='tenancy_update'),
    path('tenancies/<int:pk>/moved-out/', views.tenancy_moved_out, name='tenancy_moved_out'),
    path('tenants/<int:pk>/history/', views.tenant_history, name='tenant_history'),
]