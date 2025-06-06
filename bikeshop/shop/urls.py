from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Головна сторінка магазину
    path('', views.home, name='home'),

    # Сторінка зі списком велосипедів, з можливістю фільтрації по типу через GET-параметр
    path('bikes/', views.bike_list, name='bike_list'),

    # Створення замовлення для конкретного велосипеда
    path('bikes/<int:bike_id>/order/', views.create_order, name='create_order'),

    # Сторінка успішного замовлення
    path('orders/<int:order_id>/success/', views.order_success, name='order_success'),
]
