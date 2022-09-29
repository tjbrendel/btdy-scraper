from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='btdyScraper-home'),
    path('add-race/<str:leagueUrl>/<str:seriesUrl>/', views.add, name='btdyScraper-add'),
    path('delete/<int:subsessionID>/', views.delete, name='btdyScraper-delete'),
    path('session/<str:leagueUrl>/<str:seriesUrl>/<int:subsessionID>/', views.session, name='btdyScraper-session'),
    path('update/<str:leagueUrl>/<str:seriesUrl>/<int:id>/', views.update, name='btdyScraper-update'),
    path('penalty-report/<str:leagueUrl>/<str:seriesUrl>/', views.penalty, name='btdyScraper-penalty'),
    path('dropweeks/<int:leagueID>', views.dropWeeks, name='btdyScraper-drop'),
    path('droprecord/<int:id>/', views.deleteRecord, name='btdyScraper-dropRecord'),
    path('season-standings/<str:leagueUrl>/<str:seriesUrl>/', views.seasonStandings, name='btdyScraper-seasonStandings'),
    path('profile/', views.profile, name='btdyScraper-profile'),
    path('add-league/', views.addLeague, name='btdyScraper-addLeague'),
    path('delete-league/<str:leagueUrl>/', views.deleteLeague, name='btdyScraper-deleteLeague'),
    path('edit-league/<str:leagueUrl>/', views.editLeague, name='btdyScraper-editLeague'),
    path('add-series/<str:leagueUrl>/', views.addSeries, name='btdyScraper-addSeries'),
    path('delete-series/<str:leagueUrl>/<str:seriesUrl>/', views.deleteSeries, name='btdyScraper-deleteSeries'),
    path('add-admin/<str:leagueUrl>/<str:seriesUrl>/', views.addAdmin, name='btdyScraper-addAdmin'),
]
