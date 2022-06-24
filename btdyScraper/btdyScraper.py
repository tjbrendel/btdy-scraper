import requests
import json
import hashlib
import base64

with open("sensConfig/config.json") as file:
    config = json.load(file)

class race_driver:
    def __init__(self, driver_id, name, start_position, finish_position, total_laps_lead, incidents, finish_points, subsession_id, average_lap, laps_comp):
        self.driver_id = driver_id
        self.name = name
        self.start_position = start_position
        self.finish_position = finish_position
        self.total_laps_lead = total_laps_lead
        self.incidents = incidents
        self.finish_points = finish_points
        self.laps_lead_points = 0
        self.most_laps_lead_points = 0
        self.pole_points = 0
        self.win_points = 0
        self.stage_points = 0
        self.win_flag = 0
        self.pole_flag = 0
        self.stage_flag = 0
        self.most_laps_lead_flag = 0
        self.top_five_flag = 0
        self.top_ten_flag = 0
        self.payout_amount = 0
        self.subsession_id = subsession_id
        self.average_lap = average_lap
        self.avg_lap_flag = 0
        self.laps_comp = laps_comp

class race_session:
    def __init__(self, subsession_id, race_date, track_id, track_name, lead_changes, total_cautions, caution_laps, total_laps):
        self.subsession_id = subsession_id
        self.race_date = race_date
        self.track_id = track_id
        self.track_name = track_name
        self.lead_changes = lead_changes
        self.total_cautions = total_cautions
        self.caution_laps = caution_laps
        self.green_laps = total_laps - caution_laps
        self.total_laps = total_laps

def encode_pw(username, password):
    initialHash = hashlib.sha256((password + username.lower()).encode('utf-8')).digest()

    hashInBase64 = base64.b64encode(initialHash).decode('utf-8')

    return hashInBase64

# #def payout(level, finish):
# #    if level == "champion":
#         return {
#             1: 12,
#             2: 10,
#             3: 8,
#             4: 6,
#             5: 5,
#             6: 3,
#             7: 2,
#             8: 2,
#             9: 1,
#             10: 1
#         }.get(finish, 0)
#     if level == "crown":
#         return {
# 			1: 20, 
# 			2: 15,
# 			3: 10,
# 			4: 8,
# 			5: 5,
# 			6: 4,
# 			7: 4,
# 			8: 3,
# 			9: 2,
# 			10: 2,
#             11: 1,
#             12: 1
# 		}.get(finish, 0)
#     if level == "weekly":
#         return {
# 			1: 12, 
# 			2: 10,
# 			3: 8,
# 			4: 6,
# 			5: 5,
# 			6: 3,
# 			7: 2,
# 			8: 2,
#             9: 1,
#             10: 1
# 		}.get(finish, 0)

def grabRaceData(subid):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        'email':config["IRACE_USER"],
        'password':encode_pw(config["IRACE_USER"], config["IRACE_PASS"])
    }
    sess = requests.Session()
    sess.post('https://members-ng.iracing.com/auth', headers=headers, json=data, timeout=2.0)
    race_request = sess.get(f'https://members-ng.iracing.com/data/results/get?subsession_id={subid}')
    link_data = json.loads(race_request.text)
    if 'error' in link_data.keys():
        return link_data
    else:
        raceData = sess.get(link_data['link'])
        raceData = json.loads(raceData.text)
        return raceData

def raceScraper(raceData, subid):
    #!!!!!!!!!!!!! SCHEDULE WORK !!!!!!!!!!!!!
    raceDate = raceData['start_time'].split('T')
    raceDate = raceDate[0]
    trackName = raceData['track']['track_name']
    leadChanges = raceData['num_lead_changes']
    numCautions = raceData['num_cautions']
    cautionLaps = raceData['num_caution_laps']
    totalLaps = raceData['race_summary']['laps_complete']
    trackId = raceData['track']['track_id']

    current_session = race_session(subid, raceDate, trackId, trackName, leadChanges, numCautions, cautionLaps, totalLaps)

    return current_session

def resultsScraper(raceData, subid):
    for i, dic in enumerate(raceData['session_results']):
        if dic['simsession_name'] == 'RACE':
            raceKey = i
    
    raceResults = []
    maxLaps = raceData['session_results'][raceKey]['results'][0]['laps_lead']

    for result in raceData['session_results'][raceKey]['results']:
        if result['laps_lead'] > maxLaps:
            maxLaps = result['laps_lead']

    for result in raceData['session_results'][raceKey]['results']:
        driverId = result['cust_id']
        name = result['display_name']
        startPosition = result['starting_position'] + 1
        finishPosition = result['finish_position'] + 1
        finishPoints = 43 - result['finish_position']
        lapsLead = result['laps_lead']
        incidents = result['incidents']
        averageLap = result['average_lap']
        lapsComplete = result['laps_complete']

        current_driver = race_driver(driverId, name, startPosition, finishPosition, lapsLead, incidents, finishPoints, subid, averageLap, lapsComplete)

        if lapsLead > 0:
            current_driver.laps_lead_points = 1
                
        if lapsLead == maxLaps:
            current_driver.most_laps_lead_points = 1
            current_driver.most_laps_lead_flag = 1
                
        if startPosition == 1:
            current_driver.pole_points = 1
            current_driver.pole_flag = 1
                
        if finishPosition == 1:
            current_driver.win_points = 3
            current_driver.win_flag = 1

        if finishPosition <= 5:
            current_driver.top_five_flag = 1

        if finishPosition <= 10:
            current_driver.top_ten_flag = 1

#        payout_amount = payout(payout_level, current_driver.finish_position)
#        current_driver.payout_amount = payout_amount

        raceResults.append(current_driver)

    return raceResults

def sessionStandings(sessionPoints, prevSession):
    curStanding = 1
    prevStanding = 1

    for result in sessionPoints:
        result['position'] = curStanding
        if result['position'] == 1:
            leaderPts = result['totalPoints']
        if result['position'] == 12:
            cutOffPoints = result['totalPoints']
        curStanding = curStanding + 1

        result['gapToLeader'] = result['totalPoints'] - leaderPts

    for result in prevSession:
        result['position'] = prevStanding
        prevStanding = prevStanding + 1

    for position in sessionPoints:
        for prevPosition in prevSession:
            if position['name'] == prevPosition['name']:
                position['posChange'] = prevPosition['position'] - position['position']
        
        if position['position'] == 1:
            position['gapToNext'] = 0
            prevPositionPoints = position['totalPoints']
        else:
            position['gapToNext'] = position['totalPoints'] - prevPositionPoints
            prevPositionPoints = position['totalPoints']

        position['gapToCutoff'] = position['totalPoints'] - cutOffPoints

    return sessionPoints