from django.urls import path, include
from backend.api import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/', include('backend.api.urls')),
]
