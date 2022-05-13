from django.shortcuts import render

races = [
    {
        'subsession_id':45891965,
        'race_date':'2022-10-01',
        'track_id':148,
        'lead_changes':3,
        'total_cautions':4,
        'caution_laps':20,
        'total_laps':180,
        'series':'BTDY Contender Series',
        'season':1,
    },
    {
        'subsession_id':45891666,
        'race_date':'2022-11-01',
        'track_id':153,
        'lead_changes':2,
        'total_cautions':5,
        'caution_laps':10,
        'total_laps':160,
        'series':'BTDY Cup Series',
        'season':5,
    }
]

def home(request):
    context = {
        'races':races,
        'series':races[0]['series'],
        'season':races[0]['season']
    }

    return render(request, 'home.html', context)

def add(request):
    return render(request, 'add.html', {'title':'Add a Race'})