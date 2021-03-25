from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import datetime, timezone

COURIER_TYPES = (
    ('foot', 'foot'),
    ('bike', 'bike'),
    ('car', 'car')
)


class Courier(models.Model):
    courier_id = models.IntegerField(verbose_name='Courier id', db_index=True, unique=True, primary_key=True)
    courier_type = models.CharField(verbose_name='Courier type', choices=COURIER_TYPES, max_length=10)
    regions = ArrayField(models.IntegerField(verbose_name='Regions'), blank=True)
    working_hours = ArrayField(models.CharField(verbose_name='Working hours', max_length=50), blank=True)
    earnings = models.IntegerField(verbose_name="earnings", blank=True, null=True)
    rating = models.FloatField(verbose_name="Rating", blank=True, null=True)


class Order(models.Model):
    order_id = models.IntegerField(verbose_name="Order id", db_index=True, unique=True, primary_key=True)
    weight = models.DecimalField(verbose_name="Weight", max_digits=4, decimal_places=2, validators=[
        MaxValueValidator(50.01),
        MinValueValidator(0.00)
    ])
    region = models.IntegerField(verbose_name="Region")
    delivery_hours = ArrayField(models.CharField(verbose_name='Delivery hours', max_length=50))
    is_available = models.BooleanField(verbose_name="Available", default=True, blank=True)
    assigned_type = models.CharField(verbose_name="Courier type", blank=True, max_length=10, null=True)


class ActiveCouriers(models.Model):
    active_id = models.IntegerField(verbose_name="Courier id", db_index=True, unique=True, primary_key=True)
    orders = ArrayField(models.IntegerField(verbose_name='Orders'), blank=True)
    assigned_time = models.DateTimeField(verbose_name="Assigned time", blank=True,
                                         default=datetime.now(timezone.utc).isoformat(), null=True)


class CompletedOrders(models.Model):
    order_id = models.IntegerField(verbose_name="Order id", db_index=True, unique=True, primary_key=True)
    courier_id = models.IntegerField(verbose_name="Courier id")
    complete_time = models.DateTimeField(verbose_name="Complete time", blank=True,
                                         default=datetime.now(timezone.utc).isoformat())
