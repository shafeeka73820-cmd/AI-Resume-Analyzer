from django.urls import path, include
from api import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/', include('api.urls')),
]
