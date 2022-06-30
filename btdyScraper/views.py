from django.shortcuts import render, redirect
from .models import raceSession, points
from django.contrib import messages
from .btdyScraper import grabRaceData, raceScraper, resultsScraper, sessionStandings
from django.db.models import Avg, Max, Sum, Count
from django.contrib.auth.decorators import login_required

def home(request):
    maxRound = points.objects.aggregate(Max('roundNum')).get('roundNum__max')
    if(maxRound is None):
        context = {
            'sessions':"No Races Yet!",
            'seasonStandings':"No Races Yet!",
        }

        return render(request, 'home.html', context)
    else:
        prevRound = maxRound - 1
        sessionPoints = (
            points.objects.values('name')
            .annotate(
                totalPoints = Sum('totalPoints'),
                starts = Count('startPosition'),
                avgStart = Avg('startPosition'),
                avgFinish = Avg('finishPosition'),
                poles = Sum('poleFlag'),
                wins = Sum('winFlag'),
                top5s = Sum('topFiveFlag'),
                top10s = Sum('topTenFlag'),
                incidents = Sum('incidents'),
                payout = Sum('payoutAmount')
            )
            .order_by('-totalPoints', 'avgFinish')
        )
        prevSession = (
            points.objects
            .values('name')
            .filter(roundNum__lte = prevRound)
            .annotate(
                totalPoints = Sum('totalPoints'),
                avgFinish = Avg('finishPosition')
            )
            .order_by('-totalPoints', 'avgFinish')
        )

        if maxRound > 10:
            for pointsRow in sessionPoints:
                dropPoints = points.objects.all().filter(name = pointsRow['name']).order_by('totalPoints')[:2]

                totalDrop = 0
                for row in dropPoints:
                    totalDrop = totalDrop + row.totalPoints
                
                pointsRow['totalPoints'] -= totalDrop

            for prevPointsRow in prevSession:
                prevDropPoints = points.objects.all().filter(name = prevPointsRow['name'], roundNum__lte = prevRound).order_by('totalPoints')[:2]

                prevTotalDrop = 0
                for row in prevDropPoints:
                    prevTotalDrop = prevTotalDrop + row.totalPoints
                
                prevPointsRow['totalPoints'] -= prevTotalDrop
            
            sessionPoints = sorted(sessionPoints, key=lambda o: o['totalPoints'], reverse=True)
            prevSession = sorted(prevSession, key=lambda o: o['totalPoints'], reverse=True)

        seasonStandings = sessionStandings(sessionPoints, prevSession)

        context = {
            'sessions':raceSession.objects.all(),
            'seasonStandings':seasonStandings,
            'maxRound': maxRound
        }

        return render(request, 'home.html', context)

@login_required
def add(request):
    rounds = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
    currentRound = points.objects.aggregate(Max('roundNum')).get('roundNum__max')

    if request.method == 'POST':
        subID = request.POST['subsessionID']
#        payout = request.POST['payout']
        series = request.POST['series']
        season = request.POST['season']
        roundNum = request.POST['roundNum']
        bonus = request.POST['bonus']
        raceData = grabRaceData(subID)
        subIDCheck = raceSession.objects.filter(subsessionID=subID)
        
        if 'error' in raceData.keys():
            messages.warning(request, 'No Subsession ID was found, check the number you entered.')
            context = {
                'title':'Add a Race',
                'sessions':raceSession.objects.all(),
                'rounds':rounds,
                'currentRound':currentRound,
            }
            return render(request, 'add.html', context)
        elif subIDCheck:
            messages.warning(request, 'Subsession ID already exists! Enter a different one.')
            context = {
                'title':'Add a Race',
                'sessions':raceSession.objects.all(),
                'rounds':rounds,
                'currentRound':currentRound,
            }
            return render(request, 'add.html', context)
        elif raceData['league_id'] != 5189:
            messages.warning(request, 'Not a BTDY Contender Series Subsession ID. Please check your number!')
            context = {
                'title':'Add a Race',
                'sessions':raceSession.objects.all(),
                'rounds':rounds,
                'currentRound':currentRound,
            }
            return render(request, 'add.html', context)
        else:    
            scrapedSession = raceScraper(raceData, subID)
            raceResults = resultsScraper(raceData, subID)
            raceSubmit = raceSession(
                subsessionID = scrapedSession.subsession_id, 
                raceDate = scrapedSession.race_date,
                trackID = scrapedSession.track_id,
                trackName = scrapedSession.track_name,
                leadChanges = scrapedSession.lead_changes,
                totalCautions = scrapedSession.total_cautions,
                cautionLaps = scrapedSession.caution_laps,
                greenLaps = scrapedSession.green_laps,
                totalLaps = scrapedSession.total_laps,
                series = series,
                season = season,
                roundNum = roundNum
            )
            raceSubmit.save()

            for driver in raceResults:
                pointsSubmit = points(
                    driverID = driver.driver_id,
                    name = driver.name,
                    startPosition = driver.start_position,
                    finishPosition = driver.finish_position,
                    totalLapsLead = driver.total_laps_lead,
                    incidents = driver.incidents,
                    finishPoints = driver.finish_points,
                    lapsLeadPoints = driver.laps_lead_points,
                    mostLapsLeadPoints = driver.most_laps_lead_points,
                    polePoints = driver.pole_points,
                    winPoints = driver.win_points,
                    stagePoints = driver.stage_points,
                    winFlag = driver.win_flag,
                    poleFlag = driver.pole_flag,
                    stageFlag = driver.stage_flag,
                    mostLapsLeadFlag = driver.most_laps_lead_flag,
                    topFiveFlag = driver.top_five_flag,
                    topTenFlag = driver.top_ten_flag,
                    payoutAmount = driver.payout_amount,
                    subsessionID = raceSubmit,
                    avgLap = driver.average_lap,
                    avgLapFlag = driver.avg_lap_flag,
                    roundNum = roundNum,
                    totalPoints = driver.finish_points + driver.laps_lead_points + driver.most_laps_lead_points + driver.pole_points + driver.win_points,
                    lapsComp = driver.laps_comp,
                    penaltyNotes = "",
                    bonusNotes = ""
                )
                
                pointsSubmit.save()

            if bonus == "incidents":
                bonusDriver = points.objects.filter(subsessionID=subID, lapsComp=scrapedSession.total_laps).order_by("incidents", "finishPosition").first()
                bonusDriver.bonusNotes = "Least Incidents"
                bonusDriver.payoutAmount += 5
                bonusDriver.save()
            elif bonus == "fastavg":
                bonusDriver = points.objects.filter(subsessionID=subID, lapsComp=scrapedSession.total_laps).order_by("avgLap", "finishPosition").first()
                bonusDriver.bonusNotes = "Fastest Avg"
                bonusDriver.payoutAmount += 5
                bonusDriver.save()
            elif bonus == "pole":
                bonusDriver = points.objects.filter(subsessionID=subID, startPosition=1).first()
                bonusDriver.bonusNotes = "Pole"
                bonusDriver.payoutAmount += 5
                bonusDriver.save()

            messages.success(request, f'Success! Race data entered for {scrapedSession.subsession_id} at {scrapedSession.track_name}. Make any edits below.')
            return redirect('btdyScraper-session', subID)
    elif(currentRound is None):
        currentRound = 1
        context = {
            'title':'Add a Race',
            'sessions':"No Races Yet!",
            'rounds':rounds,
            'currentRound':currentRound,
        }

        return render(request, 'add.html', context)
    else:
        currentRound += 1
        context = {
            'title':'Add a Race',
            'sessions':raceSession.objects.all(),
            'rounds':rounds,
            'currentRound':currentRound,
        }
        return render(request, 'add.html', context)

@login_required
def delete(request, subsessionID):
    deletedSession = raceSession.objects.get(subsessionID=subsessionID)
    deletedSession.delete()
    
    messages.success(request, f'Success! Race data deleted for {subsessionID}')
    return redirect('btdyScraper-home')

def session(request, subsessionID):
    roundNum = raceSession.objects.values('roundNum').filter(subsessionID=subsessionID).first()
    title = f"Round {roundNum['roundNum']}"

    context = {
        'selectedSession':raceSession.objects.filter(subsessionID=subsessionID).first(),
        'selectedResults':points.objects.filter(subsessionID=subsessionID),
        'sessions':raceSession.objects.all(),
        'title': title,
    }
    return render(request, 'session.html', context)

@login_required
def update(request, id):
    if request.method == 'POST':
        finishPoints = request.POST['finishPoints']
        payoutAmount = request.POST['payoutAmount']
        notes = request.POST['notes']
        next = request.POST['next']
        bonusNotes = request.POST['bonusNotes']
        updateTarget = points.objects.get(id=id)

        updateTarget.totalPoints = finishPoints
        updateTarget.payoutAmount = payoutAmount
        
        if "penalty" in request.POST:
            updateTarget.penalty = 1
        else:
            updateTarget.penalty = 0

        if notes != "":
            updateTarget.penaltyNotes = notes
        
        if bonusNotes != "":
            updateTarget.bonusNotes = bonusNotes

        updateTarget.save()

        messages.success(request, f'Success! Record updated!')
        return redirect(next)
    else:
        updateTarget = points.objects.get(id=id)
        context = {
            'updateTarget':updateTarget,
            'sessions':raceSession.objects.all(),
        }
        return render(request, 'update.html', context)

def penalty(request):
    context = {
        'penalties':points.objects.filter(penalty=1).order_by('-roundNum'),
        'sessions':raceSession.objects.all(),
        'title': 'Penalty Report'
    }
    
    return render(request, 'penalty.html', context)

def dropWeeks(request):
    nameList = points.objects.values('name').distinct()

    dropRaces = []
    for driver in nameList:
        rows = points.objects.filter(name=driver['name']).order_by('totalPoints')[:2]
        for row in rows:
            dropRaces.append(row)
    
    context = {
        'droppedRaces':dropRaces,
        'title':'Dropped Races',
        'sessions':raceSession.objects.all(),
    }

    return render(request, 'droppedRaces.html', context)

@login_required
def deleteRecord(request, id):
    next = request.POST['next']
    deletedRecord = points.objects.get(id=id)
    deletedRecord.delete()

    messages.success(request, f'Success! Record deleted!')
    return redirect(next)