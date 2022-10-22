from django.shortcuts import render, redirect
from .models import raceSession, points
from django.contrib import messages
from .btdyScraper import grabRaceData, raceScraper, resultsScraper, sessionStandings, calcDropWeeks, calcPrevDropWeeks
from django.db.models import Avg, Max, Sum, Count
from django.contrib.auth.decorators import login_required

def home(request):
    context = {
            'title': 'Home'
        }

    return render(request, 'home.html', context)

@login_required
def add(request):
    currentRound = points.objects.aggregate(Max('roundNum')).get('roundNum__max')

    if request.method == 'POST':
        subID = request.POST['subsessionID']
        payout = request.POST['payout']
        series = request.POST['series']
        season = request.POST['season']
        roundNum = request.POST['roundNum']
        bonus = request.POST['bonus']
        raceData = grabRaceData(subID)
        subIDCheck = raceSession.objects.filter(subsessionID=subID)

        if series == 'BTDY Contender Series':
            leagueID = 5189
        elif series == 'BTDY Premier Series':
            leagueID = 4333
        
        if 'error' in raceData.keys():
            messages.warning(request, 'No Subsession ID was found! check the number you entered.')
            context = {
                'title':'Add a Race',
                'sessions':raceSession.objects.all().order_by('roundNum'),
            }
            return render(request, 'add.html', context)
        elif subIDCheck:
            messages.warning(request, 'Subsession ID already exists! Enter a different one.')
            context = {
                'title':'Add a Race',
                'sessions':raceSession.objects.all().order_by('roundNum'),
            }
            return render(request, 'add.html', context)
        elif raceData['league_id'] != leagueID:
            messages.warning(request, 'Not a BTDY Series Subsession ID! Please check your number.')
            context = {
                'title':'Add a Race',
                'sessions':raceSession.objects.all().order_by('roundNum'),
            }
            return render(request, 'add.html', context)
        else:    
            scrapedSession = raceScraper(raceData, subID)
            raceResults = resultsScraper(raceData, subID, payout, series)
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
                bonusDriver.payoutAmount += 3
                bonusDriver.save()
            elif bonus == "fastavg":
                bonusDriver = points.objects.filter(subsessionID=subID, lapsComp=scrapedSession.total_laps).order_by("avgLap", "finishPosition").first()
                bonusDriver.bonusNotes = "Fastest Avg"
                bonusDriver.payoutAmount += 3
                bonusDriver.save()
            elif bonus == "pole":
                bonusDriver = points.objects.filter(subsessionID=subID, startPosition=1).first()
                bonusDriver.bonusNotes = "Pole"
                bonusDriver.payoutAmount += 3
                bonusDriver.save()

            messages.success(request, f'Success! Race data entered for {scrapedSession.subsession_id} at {scrapedSession.track_name}. Make any edits below.')
            return redirect('btdyScraper-session', leagueID, subID)
    elif(currentRound is None):
        context = {
            'title':'Add a Race',
            'sessions':"No Races Yet!",
        }

        return render(request, 'add.html', context)
    else:
        context = {
            'title':'Add a Race',
            'sessions':raceSession.objects.all().order_by('roundNum'),
        }
        return render(request, 'add.html', context)

@login_required
def delete(request, subsessionID):
    deletedSession = raceSession.objects.get(subsessionID=subsessionID)
    deletedSession.delete()
    
    messages.success(request, f'Success! Race data deleted for {subsessionID}')
    return redirect('btdyScraper-home')

def session(request, leagueID, subsessionID):
    if leagueID == 5189:
        #contender
        seriesFilter = 'BTDY Contender Series'
    elif leagueID == 4333:
        #premier
        seriesFilter = 'BTDY Premier Series'
    
    roundNum = raceSession.objects.values('roundNum').filter(subsessionID=subsessionID,series=seriesFilter).first()
    title = f"Round {roundNum['roundNum']}"

    context = {
        'selectedSession':raceSession.objects.filter(subsessionID=subsessionID, series=seriesFilter).first(),
        'selectedResults':points.objects.filter(subsessionID=subsessionID, subsessionID__series=seriesFilter),
        'sessions':raceSession.objects.filter(series=seriesFilter).all().order_by('roundNum'),
        'title': title,
        'leagueID': leagueID
    }
    return render(request, 'session.html', context)

@login_required
def update(request, leagueID, id):
    if leagueID == 5189:
        #contender
        seriesFilter = 'BTDY Contender Series'
    elif leagueID == 4333:
        #premier
        seriesFilter = 'BTDY Premier Series'
    
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
            'sessions':raceSession.objects.filter(series=seriesFilter).all().order_by('roundNum'),
            'leagueID': leagueID
        }
        return render(request, 'update.html', context)

def penalty(request, leagueID):
    if leagueID == 5189:
        #contender
        seriesFilter = 'BTDY Contender Series'
    elif leagueID == 4333:
        #premier
        seriesFilter = 'BTDY Premier Series'

    context = {
        'penalties':points.objects.filter(penalty=1, subsessionID__series = seriesFilter).order_by('-roundNum'),
        'sessions':raceSession.objects.filter(series = seriesFilter).all().order_by('roundNum'),
        'title': 'Penalty Report',
        'series': raceSession.objects.filter(series = seriesFilter).values("series").first(),
        'leagueID': leagueID
    }
    
    return render(request, 'penalty.html', context)

def dropWeeks(request, leagueID):
    if leagueID == 5189:
        #contender
        seriesFilter = 'BTDY Contender Series'
    elif leagueID == 4333:
        #premier
        seriesFilter = 'BTDY Premier Series'
    nameList = points.objects.filter(subsessionID__series = seriesFilter).values('name').distinct()
    maxRound = points.objects.filter(subsessionID__series = seriesFilter).aggregate(Max('roundNum')).get('roundNum__max')
    dropRaces = []

    for driver in nameList:
        starts = points.objects.filter(name=driver['name'], subsessionID__series=seriesFilter).count()
        if leagueID == 5189 and starts == maxRound:
            rows = points.objects.filter(name=driver['name'], subsessionID__series=seriesFilter).order_by('totalPoints')[:2]
            for row in rows:
                dropRaces.append(row)
        elif (leagueID == 5189 and starts == maxRound-1) or (leagueID == 4333 and starts == maxRound):
            rows = points.objects.filter(name=driver['name'], subsessionID__series=seriesFilter).order_by('totalPoints')[:1]
            for row in rows:
                dropRaces.append(row)
    
    context = {
        'droppedRaces':dropRaces,
        'title':'Dropped Races',
        'sessions':raceSession.objects.filter(series = seriesFilter).all().order_by('roundNum'),
        'series': raceSession.objects.filter(series = seriesFilter).values("series").first(),
        'leagueID': leagueID
    }

    return render(request, 'droppedRaces.html', context)

@login_required
def deleteRecord(request, id):
    next = request.POST['next']
    deletedRecord = points.objects.get(id=id)
    deletedRecord.delete()

    messages.success(request, f'Success! Record deleted!')
    return redirect(next)

def seasonStandings(request, leagueID):
    if leagueID == 5189:
        #contender
        seriesFilter = 'BTDY Contender Series'
    elif leagueID == 4333:
        #premier
        seriesFilter = 'BTDY Premier Series'

    maxRound = points.objects.filter(subsessionID__series = seriesFilter).aggregate(Max('roundNum')).get('roundNum__max')
    if(maxRound is None):
        context = {
            'sessions':"No Races Yet!",
            'seasonStandings':"No Races Yet!",
            'series': raceSession.objects.filter(series = seriesFilter).values("series").first()
        }

        return render(request, 'seasonStandings.html', context)
    else:
        prevRound = maxRound - 1
        sessionPoints = (
            points.objects.values('name')
            .filter(subsessionID__series = seriesFilter)
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
            .filter(
                roundNum__lte = prevRound,
                subsessionID__series = seriesFilter
            )
            .annotate(
                totalPoints = Sum('totalPoints'),
                avgFinish = Avg('finishPosition'),
                starts = Count('startPosition')
            )
            .order_by('-totalPoints', 'avgFinish')
        )

        if maxRound > 10:
            for pointsRow in sessionPoints:
                if leagueID == 4333 and pointsRow['totalPoints'] > 4999:
                    pointsRow['totalPoints'] += pointsRow['wins'] * 10
                elif leagueID == 5189 and pointsRow['starts'] == maxRound:
                    totalDrop = calcDropWeeks(pointsRow, seriesFilter, 2)
                    pointsRow['totalPoints'] -= totalDrop
                elif (leagueID == 5189 and pointsRow['starts'] == maxRound-1) or (leagueID == 4333 and pointsRow['starts'] == maxRound):
                    totalDrop = calcDropWeeks(pointsRow, seriesFilter, 1)
                    pointsRow['totalPoints'] -= totalDrop

            for prevPointsRow in prevSession:
                if pointsRow['totalPoints'] > 999:
                    pointsRow['totalPoints'] += pointsRow['wins'] * 10
                elif leagueID == 5189 and prevPointsRow['starts'] == prevRound:
                    prevTotalDrop = calcPrevDropWeeks(prevPointsRow, prevRound, seriesFilter, 2)
                    prevPointsRow['totalPoints'] -= prevTotalDrop
                elif (leagueID == 5189 and prevPointsRow['starts'] == prevRound-1) or (leagueID == 4333 and pointsRow['starts'] == prevRound):
                    prevTotalDrop = calcPrevDropWeeks(prevPointsRow, prevRound, seriesFilter, 1)
                    prevPointsRow['totalPoints'] -= prevTotalDrop
            
            sessionPoints = sorted(sessionPoints, key=lambda o: (o['totalPoints'], -o['avgFinish']), reverse=True)
            prevSession = sorted(prevSession, key=lambda o: (o['totalPoints'], -o['avgFinish']), reverse=True)

        seasonStandings = sessionStandings(sessionPoints, prevSession)

        context = {
            'sessions':raceSession.objects.filter(series = seriesFilter).all().order_by('roundNum'),
            'seasonStandings':seasonStandings,
            'maxRound': maxRound,
            'series': raceSession.objects.filter(series = seriesFilter).values("series").first(),
            'leagueID': leagueID
        }

        return render(request, 'seasonStandings.html', context)

def seriesStats(request):
    context = {
        'title': 'Series Stats'
    }
    return render(request, 'seriesStats.html', context)