from django.urls import path, include
from api import views

urlpatterns = [
    path('api/', include('api.urls')),
    path('', views.home, name='home'), # Maps root to home view
]
