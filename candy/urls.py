from django.urls import path
from candy.views import *

urlpatterns = [
    path('couriers', CreateCourier.as_view()),
    path('couriers/<int:pk>', PatchCourier.as_view()),
    path('orders', CreateOrders.as_view()),
    path('orders/assign', Assign.as_view()),
    path('orders/complete', CompleteOrder.as_view())
]
