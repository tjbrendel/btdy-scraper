from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='btdyScraper-home'),
    path('add/', views.add, name='btdyScraper-add'),
    path('delete/<int:subsessionID>/', views.delete, name='btdyScraper-delete'),
    path('session/<int:subsessionID>/', views.session, name='btdyScraper-session'),
    path('update/<int:id>/', views.update, name='btdyScraper-update'),
    path('penalty/', views.penalty, name='btdyScraper-penalty'),
    path('dropweeks/', views.dropWeeks, name='btdyScraper-drop'),
    path('droprecord/<int:id>/', views.deleteRecord, name='btdyScraper-dropRecord')
]
