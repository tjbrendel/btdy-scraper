from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='btdyScraper-home'),
    path('add/', views.add, name='btdyScraper-about')
]
