import argparse
import csv
import sys
import time
import calendar

import googleapiclient.discovery
import requests as requests

parser = argparse.ArgumentParser()
parser.add_argument("EventKey", help="Event Key (e.g. 2021txcls)")
parser.add_argument("-t", dest='Twitch', help="Vod Id(s) (e.g. twitch.tv/videos/[VOD_ID]. "
                               "For multiple entries, separate them with a comma without spaces")
parser.add_argument("-y", dest='Youtube', help="Youtube Video(s) (e.g. https://www.youtube.com/watch?v=[VIDEO_ID]]. "
                               "For multiple entries, separate them with a comma without spaces")
args = parser.parse_args()


def main():
    if not args.EventKey:
        print("Error: No EventKey Argument Provided")
        return
    else:
        event_key = args.EventKey

    if not args.Twitch and not args.Youtube:
        print("Error: No video ID provided")
        return

    if args.Twitch:
        twitch_vod_ids = args.Twitch.split(",")

    if args.Youtube:
        youtube_vod_ids = args.Youtube.split(",")

    try:
        with open('TbaApiKey.txt', 'r') as fid:
            tba_key = fid.readline().strip()

        if args.Twitch:
            with open('TwitchClientId.txt', 'r') as fid:
                twitch_client_id = fid.readline().strip()

            with open('TwitchClientSecret.txt', 'r') as fid:
                twitch_client_secret = fid.readline().strip()

        if args.Youtube:
            with open('YoutubeApiKey.txt', 'r') as fid:
                youtube_api_key = fid.readline().strip()

    except IOError as e:
        print("Error: Could not get authentication keys from files")
        print(e)
        print(sys.exec_type)
        return

    tba_verify_event_url = 'https://www.thebluealliance.com/api/v3/event/{}'.format(event_key)
    tba_headers = {
        'accept': 'application/json',
        'X-TBA-Auth-Key': '{}'.format(tba_key)
    }
    tba_data = requests.get(tba_verify_event_url, headers=tba_headers).json()

    if 'Errors' in tba_data.keys():
        print("Error: Event Key not recognized. Key given: {}".format(event_key)
        return

    tba_query_url = 'https://www.thebluealliance.com/api/v3/event/{}/matches/simple'.format(event_key)
    tba_headers = {
        'accept': 'application/json',
        'X-TBA-Auth-Key': '{}'.format(tba_key)
    }

    tba_data = requests.get(tba_query_url, headers=tba_headers).json()

    match_info = {}
    match_times = {}
    for match in tba_data:
        match_data = {
            'key': match['key'],
            'match_time': match['time'],
            'actual_time': match['actual_time'],
            'timestamp_type': '',
            'vod_url': ''
        }

        if match['actual_time']:
            match_times[match['key']] = match['actual_time']
            match_data['timestamp_type'] = 'actual_time'
        elif match['time']:
            match_times[match['key']] = match['time']
            match_data['timestamp_type'] = 'scheduled_time'
        else:
            match_times[match['key']] = 0
            match_data['timestamp_type'] = 'N/A'
        match_info[match['key']] = match_data

    if args.Twitch:
        processTwitchVideos(twitch_client_id, twitch_client_secret, twitch_vod_ids, event_key, match_times, match_info)

    if args.Youtube:
        processYoutubeVideos(youtube_api_key, youtube_vod_ids, event_key, match_times, match_info)

    return


def processTwitchVideos(twitch_client_id, twitch_client_secret, twitch_vod_ids, event_key, match_times, match_info):
    # Twitch Client Authorization
    twitch_authorization_url = 'https://id.twitch.tv/oauth2/token'
    twitch_authorization_url += '?client_id={}'.format(twitch_client_id)
    twitch_authorization_url += '&client_secret={}'.format(twitch_client_secret)
    twitch_authorization_url += '&grant_type=client_credentials'

    twitch_authorization_response = requests.post(twitch_authorization_url).json()

    twitch_access_token = twitch_authorization_response['access_token']

    twitch_vod_headers = {
        "Authorization": "Bearer {}".format(twitch_access_token),
        "Client-Id": twitch_client_id
    }

    # Get vod info using Twitch's API
    vod_start_times = {}
    vod_end_times = {}
    for vodId in twitch_vod_ids:
        twitch_vod_info_url = 'https://api.twitch.tv/helix/videos?id={}'.format(vodId)
        twitch_vod_info = requests.get(twitch_vod_info_url, headers=twitch_vod_headers).json()

        vod_start_time = twitch_vod_info['data'][0]['created_at']
        vod_duration = '1970-1-1T{}'.format(twitch_vod_info['data'][0]['duration'])
        vod_duration_unix = calendar.timegm(time.strptime(vod_duration, "%Y-%m-%dT%Hh%Mm%Ss"))
        vod_start_times[vodId] = calendar.timegm(time.strptime(vod_start_time, "%Y-%m-%dT%H:%M:%SZ"))
        vod_end_times[vodId] = vod_start_times[vodId] + vod_duration_unix

    sorted_vods_by_timestamp = {k: v for k, v in sorted(vod_start_times.items(), key=lambda item: item[1])}

    # TBA timestamps are ~ 24 hours ahead of Twitch timestamps?
    tba_unix_offset = 24 * 3600

    for matchId in match_times:
        match_times[matchId] = match_times[matchId] - tba_unix_offset

    for vodId in sorted_vods_by_timestamp:
        vod_start_time = sorted_vods_by_timestamp[vodId]
        vod_end_time = vod_end_times[vodId] + tba_unix_offset
        vod_matches = dict((k, v) for k, v in match_times.items() if v >= vod_start_time)
        vod_matches = dict((k, v) for k, v in vod_matches.items() if v <= vod_end_time)

        for matchKey in vod_matches:
            if match_times[matchKey] == 0:
                match_info[matchKey]['vod_url'] = 'N/A'
                continue

            time_offset = match_times[matchKey] - vod_start_time
            seconds = time_offset % 60
            minutes_raw = (time_offset - seconds) / 60
            minutes = minutes_raw % 60
            hours = (minutes_raw - minutes) / 60
            time_offset_string = '{}h{}m{}s'.format(str(int(hours)), str(int(minutes)), str(int(seconds)))
            match_info[matchKey]['vod_url'] = 'https://www.twitch.tv/videos/{}?t={}'.format(vodId, time_offset_string)

    writeToCsv(event_key, match_info)

    return


def processYoutubeVideos(youtube_api_key, youtube_vod_ids, event_key, match_times, match_info):
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "YoutubeApiKey.txt"

    # Get credentials and create an API client
    youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=youtube_api_key)

    vod_start_times = {}
    vod_end_times = {}
    for vodId in youtube_vod_ids:
        request = youtube.videos().list(
            part="liveStreamingDetails,contentDetails",
            id=vodId
        )
        youtube_video_info = request.execute()

        vod_start_time = youtube_video_info['items'][0]['liveStreamingDetails']['actualStartTime']
        vod_duration = '1970-1-1T{}'.format(youtube_video_info['items'][0]['contentDetails']['duration'])
        vod_duration_unix = calendar.timegm(time.strptime(vod_duration, "%Y-%m-%dTPT%HH%MM%SS"))
        vod_start_times[vodId] = calendar.timegm(time.strptime(vod_start_time, "%Y-%m-%dT%H:%M:%SZ"))
        vod_end_times[vodId] = vod_start_times[vodId] + vod_duration_unix

    sorted_vods_by_timestamp = {k: v for k, v in sorted(vod_start_times.items(), key=lambda item: item[1])}

    tba_unix_offset = 0

    for matchId in match_times:
        match_times[matchId] = match_times[matchId] - tba_unix_offset

    for vodId in sorted_vods_by_timestamp:
        vod_start_time = sorted_vods_by_timestamp[vodId]
        vod_end_time = vod_end_times[vodId] + tba_unix_offset
        vod_matches = dict((k, v) for k, v in match_times.items() if v >= vod_start_time)
        vod_matches = dict((k, v) for k, v in vod_matches.items() if v <= vod_end_time)

        for matchKey in vod_matches:
            if match_times[matchKey] == 0:
                match_info[matchKey]['vod_url'] = 'N/A'
                continue

            time_offset = match_times[matchKey] - vod_start_time
            seconds = time_offset
            time_offset_string = '{}s'.format(str(int(seconds)))
            match_info[matchKey]['vod_url'] = 'https://www.youtube.com/watch?v={}&t={}'.format(vodId, time_offset_string)

    writeToCsv(event_key, match_info)

    return


def writeToCsv(event_key, match_info):
    filename = '{}_vodTimestamps.csv'.format(event_key)
    fields = ['matchKey', 'timestampType', 'vodUrl']

    with open(filename, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(fields)

        for matchKey in match_info:
            vod_url = match_info[matchKey]['vod_url']
            timestamp_type = match_info[matchKey]['timestamp_type']
            if not vod_url:
                vod_url = 'N/A'

            writer.writerow([matchKey, timestamp_type, vod_url])

    print("Done! Results saved to {}".format(filename))

    return


if __name__ == '__main__':
    main()

