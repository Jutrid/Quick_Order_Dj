from django.urls import path
from order_app import views

urlpatterns = [
    path('order/list', views.order_list, name='order_list'),
    path('clients/list', views.clients_list, name='clients_list'),
]