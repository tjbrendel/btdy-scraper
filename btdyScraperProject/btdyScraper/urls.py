from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='btdyScraper-home'),
    path('about/', views.about, name='btdyScraper-about')
]
