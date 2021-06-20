import argparse
import csv
import datetime
import json
import time
import calendar

import requests as requests

parser = argparse.ArgumentParser()
parser.add_argument("EventKey", help="Event Key (e.g. 2021txcls)")
parser.add_argument("TwitchVodIds", help="Vod Id(s) (e.g. twitch.tv/videos/[VOD_ID]. Separate them with a space", nargs='*')
args = parser.parse_args()

def main():
    if not args.EventKey:
        print("Error: No EventKey Argument Provided")
        return
    else:
        eventKey = args.EventKey

    if not args.TwitchVodIds:
        print("Error: No Twitch Vod Id Provided")
        return
    else:
        twitchVodIds = args.TwitchVodIds

    try:
        with open('TbaApiKey.txt', 'r') as fid:
            tbaKey = fid.readline().strip()

        with open('TwitchClientId.txt', 'r') as fid:
            twitchClientId = fid.readline().strip()

        with open('TwitchClientSecret.txt', 'r') as fid:
            twitchClientSecret = fid.readline().strip()

    except IOError as e:
        print("Error: Could not get authentication keys from files")
        print(e)
        prin(sys.exec_type)
        return

    tbaVerifyEventUrl = 'https://www.thebluealliance.com/api/v3/event/{}'.format(eventKey)
    tbaHeaders = {
        'accept': 'application/json',
        'X-TBA-Auth-Key': '{}'.format(tbaKey)
    }
    tbaData = requests.get(tbaVerifyEventUrl, headers=tbaHeaders).json()

    if tbaData['Errors']:
        print("Error: Event Key Invalid. Event Key Provided: {}".format(eventKey))
        return

    tbaQueryUrl = 'https://www.thebluealliance.com/api/v3/event/{}/matches/simple'.format(eventKey)
    tbaHeaders = {
        'accept': 'application/json',
        'X-TBA-Auth-Key': '{}'.format(tbaKey)
    }

    tbaData = requests.get(tbaQueryUrl, headers=tbaHeaders).json()

    matchInfo = {}
    matchTimes = {}
    for match in tbaData:
        matchData = {
            'key': match['key'],
            'match_time': match['time'],
            'actual_time': match['actual_time'],
            'timestamp_type': '',
            'vod_url': ''
        }

        if match['actual_time']:
            matchTimes[match['key']] = match['actual_time']
            matchData['timestamp_type'] = 'actual_time'
        elif match['time']:
            matchTimes[match['key']] = match['time']
            matchData['timestamp_type'] = 'scheduled_time'
        else:
            matchTimes[match['key']] = 0
            matchData['timestamp_type'] = 'N/A'
        matchInfo[match['key']] = matchData

    # Twitch Client Authorization
    twitchAuthorizationUrl = 'https://id.twitch.tv/oauth2/token'
    twitchAuthorizationUrl += '?client_id={}'.format(twitchClientId)
    twitchAuthorizationUrl += '&client_secret={}'.format(twitchClientSecret)
    twitchAuthorizationUrl += '&grant_type=client_credentials'

    twitchAuthorizationResponse = requests.post(twitchAuthorizationUrl).json()

    twitchAccessToken = twitchAuthorizationResponse['access_token']

    twitchVodHeaders = {
        "Authorization": "Bearer {}".format(twitchAccessToken),
        "Client-Id": twitchClientId
    }

    # Get vod info using Twitch's API
    vodStartTimes = {}
    vodEndTimes = {}
    for vodId in twitchVodIds:
        twitchVodInfoUrl = 'https://api.twitch.tv/helix/videos?id={}'.format(vodId)
        twitchVodInfo = requests.get(twitchVodInfoUrl, headers=twitchVodHeaders).json()
        vodStartTime = twitchVodInfo['data'][0]['created_at']
        vodDuration = '1970-1-1T{}'.format(twitchVodInfo['data'][0]['duration'])
        vodDurationUnix = calendar.timegm(time.strptime(vodDuration, "%Y-%m-%dT%Hh%Mm%Ss"))
        vodStartTimes[vodId] = calendar.timegm(time.strptime(vodStartTime, "%Y-%m-%dT%H:%M:%SZ"))
        vodEndTimes[vodId] = vodStartTimes[vodId] + vodDurationUnix

    sortedVodsByTimestamp = {k: v for k, v in sorted(vodStartTimes.items(), key=lambda item: item[1])}

    # TBA timestamps are ~ 24 hours ahead of Twitch timestamps?
    tbaUnixOffset = 24 * 3600

    for matchId in matchTimes:
        matchTimes[matchId] = matchTimes[matchId] - tbaUnixOffset

    for vodId in sortedVodsByTimestamp:
        vodStartTime = sortedVodsByTimestamp[vodId]
        vodEndTime = vodEndTimes[vodId] + tbaUnixOffset
        vodMatches = dict((k, v) for k, v in matchTimes.items() if v >= vodStartTime)
        vodMatches = dict((k, v) for k, v in vodMatches.items() if v <= vodEndTime)

        for matchKey in vodMatches:
            if matchTimes[matchKey] == 0:
                matchInfo[matchKey]['vod_url'] = 'N/A'
                continue

            timeOffset = matchTimes[matchKey] - vodStartTime
            seconds = timeOffset % 60
            minutesRaw = (timeOffset - seconds) / 60
            minutes = minutesRaw % 60
            hours = (minutesRaw - minutes) / 60
            timeOffsetString = '{}h{}m{}s'.format(str(int(hours)), str(int(minutes)), str(int(seconds)))
            matchInfo[matchKey]['vod_url'] = 'https://www.twitch.tv/videos/{}?t={}'.format(vodId, timeOffsetString)

    # Write to csv
    filename = '{}_vodTimestamps.csv'.format(eventKey)
    fields = ['matchKey','timestampType', 'vodUrl']

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(fields)

        for matchKey in matchInfo:
            vodUrl = matchInfo[matchKey]['vod_url']
            timestampType = matchInfo[matchKey]['timestamp_type']
            if not vodUrl:
                vodUrl = 'N/A'

            writer.writerow([matchKey, timestampType, vodUrl])

    print("Done! Results saved to {}".format(filename))

    return


if __name__ == '__main__':
    main()

