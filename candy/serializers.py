from candy.models import *
from rest_framework import serializers


class CourierDetail(serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = ['courier_id', 'courier_type', 'regions', 'working_hours']


class CourierReport(serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = '__all__'


class CourierPatch(serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = ['courier_type', 'regions', 'working_hours']


class OrderDetail(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_id', "weight", "region", "delivery_hours"]


class GetCourierId(serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = ['courier_id']


class OrderFinished(serializers.ModelSerializer):
    class Meta:
        model = CompletedOrders
        fields = '__all__'
