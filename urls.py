
from django.contrib import admin
from django.urls import include
from candy.urls import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('candy.urls')),
]
