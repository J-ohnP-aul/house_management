from django.urls import path
from . import views

urlpatterns = [
    path('', views.maintenance_list, name='m_list'),                     
    path('create/', views.maintenance_create, name='m_create'),          
    path('<int:pk>/', views.maintenance_detail, name='m_detail'),        
    path('<int:pk>/update/', views.maintenance_update, name='m_update'), 
    path('<int:pk>/delete/', views.maintenance_delete, name='m_delete'), 
]