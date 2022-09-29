from django.shortcuts import render, redirect
from .models import raceSession, points, league, series
from django.contrib import messages
from .btdyScraper import grabRaceData, raceScraper, resultsScraper, sessionStandings, calcDropWeeks, calcPrevDropWeeks, leagueOwnerCheck
from django.db.models import Avg, Max, Sum, Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

def home(request):
    context = {
            'title': 'Home'
        }

    return render(request, 'home.html', context)

@login_required
def add(request, leagueUrl, seriesUrl):
    if request.method == 'POST':
        toAddSubID = request.POST['subsessionID']
        toAddPayout = request.POST['payout']
        toAddSeason = request.POST['season']
        toAddRoundNum = request.POST['roundNum']
        toAddBonus = request.POST['bonus']
        raceData = grabRaceData(toAddSubID)
        subIDCheck = raceSession.objects.filter(subsessionID=toAddSubID)

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
        else:    
            scrapedSession = raceScraper(raceData, toAddSubID)
            raceResults = resultsScraper(raceData, toAddSubID, toAddPayout, series)
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
                seriesID = series.objects.get(leagueID__leagueUrl=leagueUrl, seriesUrl = seriesUrl),
                season = toAddSeason,
                roundNum = toAddRoundNum
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
                    roundNum = toAddRoundNum,
                    totalPoints = driver.finish_points + driver.laps_lead_points + driver.most_laps_lead_points + driver.pole_points + driver.win_points,
                    lapsComp = driver.laps_comp,
                    penaltyNotes = "",
                    bonusNotes = ""
                )
                
                pointsSubmit.save()

            if toAddBonus == "incidents":
                bonusDriver = points.objects.filter(subsessionID=toAddSubID, lapsComp=scrapedSession.total_laps).order_by("incidents", "finishPosition").first()
                bonusDriver.bonusNotes = "Least Incidents"
                bonusDriver.payoutAmount += 3
                bonusDriver.save()
            elif toAddBonus == "fastavg":
                bonusDriver = points.objects.filter(subsessionID=toAddSubID, lapsComp=scrapedSession.total_laps).order_by("avgLap", "finishPosition").first()
                bonusDriver.bonusNotes = "Fastest Avg"
                bonusDriver.payoutAmount += 3
                bonusDriver.save()
            elif toAddBonus == "pole":
                bonusDriver = points.objects.filter(subsessionID=toAddSubID, startPosition=1).first()
                bonusDriver.bonusNotes = "Pole"
                bonusDriver.payoutAmount += 3
                bonusDriver.save()

            messages.success(request, f'Success! Race data entered for {scrapedSession.subsession_id} at {scrapedSession.track_name}. Make any edits below.')
            return redirect('btdyScraper-session', leagueUrl, seriesUrl, toAddSubID)
    else:
        currentRound = points.objects.filter(subsessionID__seriesID__leagueID__leagueUrl=leagueUrl, subsessionID__seriesID__seriesUrl = seriesUrl).aggregate(Max('roundNum')).get('roundNum__max')
        if currentRound is None:
            context = {
                'title':'Add a Race',
                'sessions':'No Races Yet!',
            }
        else:
            context = {
                'title':'Add a Race',
                'sessions':raceSession.objects.filter(seriesID__leagueID__leagueUrl=leagueUrl, seriesID__seriesUrl = seriesUrl).order_by('roundNum'),
                'series':series.objects.get(leagueID__leagueUrl=leagueUrl, seriesUrl = seriesUrl)
            }
        
        return render(request, 'add.html', context)

@login_required
def delete(request, subsessionID):
    deletedSession = raceSession.objects.get(subsessionID=subsessionID)
    deletedSession.delete()
    
    messages.success(request, f'Success! Race data deleted for {subsessionID}')
    return redirect('btdyScraper-home')

def session(request, leagueUrl, seriesUrl, subsessionID):
    roundNum = raceSession.objects.get(subsessionID=subsessionID)
    title = f"Round {roundNum}"

    context = {
        'selectedSession':raceSession.objects.filter(subsessionID=subsessionID).first(),
        'selectedResults':points.objects.filter(subsessionID=subsessionID),
        'sessions':raceSession.objects.filter(seriesID__leagueID__leagueUrl=leagueUrl, seriesID__seriesUrl = seriesUrl).order_by('roundNum'),
        'title': title
    }
    return render(request, 'session.html', context)

@login_required
def update(request, leagueUrl, seriesUrl, id):
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
            'sessions':raceSession.objects.filter(seriesID__leagueID__leagueUrl=leagueUrl, seriesID__seriesUrl = seriesUrl).order_by('roundNum')
        }
        return render(request, 'update.html', context)

def penalty(request, leagueUrl, seriesUrl):
    context = {
        'penalties':points.objects.filter(
            penalty=1, 
            subsessionID__seriesID__leagueID__leagueUrl=leagueUrl, 
            subsessionID__seriesID__seriesUrl=seriesUrl).order_by('-roundNum'),
        'sessions':raceSession.objects.filter(seriesID__leagueID__leagueUrl=leagueUrl, seriesID__seriesUrl = seriesUrl).order_by('roundNum'),
        'title': 'Penalty Report',
        'series': series.objects.get(leagueID__leagueUrl=leagueUrl, seriesUrl = seriesUrl)
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

def seasonStandings(request, leagueUrl, seriesUrl):
    maxRound = points.objects.filter(subsessionID__seriesID__leagueID__leagueUrl= leagueUrl, subsessionID__seriesID__seriesUrl=seriesUrl).aggregate(Max('roundNum')).get('roundNum__max')
    if(maxRound is None):
        context = {
            'sessions':"No Races Yet!",
            'seasonStandings':"No Races Yet!",
            'series': series.objects.get(seriesUrl = seriesUrl, leagueID__leagueUrl = leagueUrl)
        }

        return render(request, 'seasonStandings.html', context)
    else:
        prevRound = maxRound - 1
        sessionPoints = (
            points.objects.values('name')
            .filter(subsessionID__seriesID__leagueID__leagueUrl=leagueUrl, subsessionID__seriesID__seriesUrl=seriesUrl)
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
                subsessionID__seriesID__leagueID__leagueUrl=leagueUrl, 
                subsessionID__seriesID__seriesUrl = seriesUrl
            )
            .annotate(
                totalPoints = Sum('totalPoints'),
                avgFinish = Avg('finishPosition'),
                starts = Count('startPosition')
            )
            .order_by('-totalPoints', 'avgFinish')
        )

        # if maxRound > 10:
        #     for pointsRow in sessionPoints:
        #         if leagueID == 5189 and pointsRow['starts'] == maxRound:
        #             totalDrop = calcDropWeeks(pointsRow, seriesFilter, 2)
        #             pointsRow['totalPoints'] -= totalDrop
        #         elif (leagueID == 5189 and pointsRow['starts'] == maxRound-1) or (leagueID == 4333 and pointsRow['starts'] == maxRound):
        #             totalDrop = calcDropWeeks(pointsRow, seriesFilter, 1)
        #             pointsRow['totalPoints'] -= totalDrop

        #     for prevPointsRow in prevSession:
        #         if leagueID == 5189 and prevPointsRow['starts'] == prevRound:
        #             prevTotalDrop = calcPrevDropWeeks(prevPointsRow, prevRound, seriesFilter, 2)
        #             prevPointsRow['totalPoints'] -= prevTotalDrop
        #         elif (leagueID == 5189 and prevPointsRow['starts'] == prevRound-1) or (leagueID == 4333 and pointsRow['starts'] == prevRound):
        #             prevTotalDrop = calcPrevDropWeeks(prevPointsRow, prevRound, seriesFilter, 1)
        #             prevPointsRow['totalPoints'] -= prevTotalDrop
            
        #     sessionPoints = sorted(sessionPoints, key=lambda o: (o['totalPoints'], -o['avgFinish']), reverse=True)
        #     prevSession = sorted(prevSession, key=lambda o: (o['totalPoints'], -o['avgFinish']), reverse=True)

        seasonStandings = sessionStandings(sessionPoints, prevSession)

        context = {
            'sessions': raceSession.objects.filter(seriesID__leagueID__leagueUrl=leagueUrl, seriesID__seriesUrl = seriesUrl).order_by('roundNum'),
            'seasonStandings': seasonStandings,
            'maxRound': maxRound,
            'series': series.objects.get(seriesUrl = seriesUrl, leagueID__leagueUrl = leagueUrl)
        }

        return render(request, 'seasonStandings.html', context)

@login_required
def addLeague(request):
    if request.method == 'POST':
        try:
            obj = league.objects.get(leagueName=request.POST['leagueName'])
            messages.warning(request, f'A league with that name already exists! Choose a different name.')
            return redirect('btdyScraper-profile')
        except:        
            formleagueOwner = request.user
            leagueSubmit = league(
                leagueName = request.POST['leagueName'],
                leagueOwner = formleagueOwner,
                leagueUrl = request.POST['leagueName'].replace(' ', '-')
            )
            
            leagueSubmit.save()

            messages.success(request, f'Success! League Created!')
            context = {
                'title': 'Create a League'
            }

            return redirect('btdyScraper-profile')
    else:
        context = {
            'title': 'Create a League'
        }

        return render(request, 'addLeague.html', context)

@login_required
def editLeague(request, leagueUrl):
    if request.method == 'POST':
        league.objects.filter(leagueUrl=leagueUrl).update(leagueName=request.POST['leagueName'], leagueUrl=request.POST['leagueName'].replace(' ', '-'))
        messages.success(request, f'Success! The league has been updated.')
        return redirect('btdyScraper-profile')
    else:
        if leagueOwnerCheck(request.user, leagueUrl):
            context = {
                'title': 'Edit League',
                'leagueToEdit': league.objects.get(leagueUrl = leagueUrl)
            }
        
            return render(request, 'editLeague.html', context)
        else:
            messages.warning(request, f'You do not own this league!')
            return redirect('btdyScraper-profile')

@login_required
def addSeries(request, leagueUrl):
    if request.method == 'POST':
        seriesName = request.POST['seriesName']
        if 'payouts' in request.POST:
            payouts = 1
        else:
            payouts = 0
        if 'bonuses' in request.POST:
            bonuses = 1
        else:
            bonuses = 0

        seriesSubmit = series(
            seriesName = seriesName,
            seriesUrl = seriesName.replace(' ', '-'),
            leagueID = league.objects.get(leagueUrl=leagueUrl),
            payoutFlag = payouts,
            bonusFlag = bonuses
        )
        seriesSubmit.save()
        seriesSubmit.admins.add(request.user)

        messages.success(request, f'Success! Series Created!')
        return redirect('btdyScraper-profile')  
    else:
        if leagueOwnerCheck(request.user, leagueUrl):
            context = {
                'title': 'Create a Series'
            }

            return render(request, 'addSeries.html', context)
        else:
            messages.warning(request, f'You do not own that league!')
            return redirect('btdyScraper-profile')

@login_required
def profile(request):
    listOfSeries = series.objects.all().filter(admins = request.user).order_by('leagueID__leagueName', 'seriesName')
    if len(listOfSeries) == 0:
        listOfSeries = None
    listOfLeagues = league.objects.all().filter(leagueOwner = request.user).order_by('leagueName')
    if len(listOfLeagues) == 0:
        listOfLeagues = None

    context = {
        'title': 'Profile',
        'leagues': listOfLeagues,
        'series': listOfSeries
    }

    return render(request, 'profile.html', context)

@login_required
def addAdmin(request, leagueUrl, seriesUrl):
    if request.method == 'POST':
        try:
            adminToAddToSeries = User.objects.get(username=request.POST['adminUserName'])
            seriesToAddAdminTo = series.objects.get(leagueID__leagueUrl=leagueUrl, seriesUrl=seriesUrl)

            seriesToAddAdminTo.admins.add(adminToAddToSeries)
            messages.success(request, f'Success! Admin Added!')
            return redirect('btdyScraper-profile')
        except:
            context = {
                'title': 'Add Admin'
            }
            messages.warning(request, f'Username does not exist! Check your spelling.')  
            return render(request, 'addAdmin.html', context)
    else:
        if leagueOwnerCheck(request.user, leagueUrl):
            context = {
                'title': 'Add Admin'
            }
            return render(request, 'addAdmin.html', context)
        else:
            messages.warning(request, f'You do not own that league!')
            return redirect('btdyScraper-profile')

@login_required
def deleteSeries(request, leagueUrl, seriesUrl):
    if leagueOwnerCheck(request.user, leagueUrl):    
        seriesToDelete = series.objects.get(leagueID__leagueUrl=leagueUrl, seriesUrl=seriesUrl)
        seriesToDelete.delete()
        messages.success(request, f'Success! Series Deleted!')
    else:
        messages.warning(request, f'You do not own that league!')
        
    return redirect('btdyScraper-profile')

@login_required
def deleteLeague(request, leagueUrl):
    if leagueOwnerCheck(request.user, leagueUrl):
        leagueToDelete = league.objects.get(leagueUrl=leagueUrl)
        leagueToDelete.delete()
        messages.success(request, f'Success! League Deleted!')
    else:
        messages.warning(request, f'You do not own that league!')

    return redirect('btdyScraper-profile')