# FrcMatchTimes

Tool to get timestamps for matches from Twitch Vods or Youtube livestream recordings to view. This tries to match the match time taken from TheBlueAlliance to generate the appropriate URLs for Twitch/Youtube to watch the match given the provided Twitch Vod IDs/Youtube Video IDs. This tries to use the actual match time if it is given and falls back to the scheduled match time if no actual match time is given. Note that if the url is generated using the scheduled match time, it will most likely be off. 


[Chief Delphi Thread](https://www.chiefdelphi.com/t/automated-access-to-match-videos-from-recorded-livestreams/394815)

## Requirements:

This is written in Python3.

You need to create text files in the base directory with their appropriate keys. Note that these should be kept private to avoid potential abuse:

**TbaApiKey.txt**

Obtained by creating an account on TheBlueAlliance and accessing your account page (https://www.thebluealliance.com/account). Generate a Read API Key and put it in this file.


### For Twitch Vods:

**TwitchClientId.txt**

Obtained by creating an application on Twitch (https://dev.twitch.tv/console/apps). Copy the Client ID into this file.

**TwitchClientSecret.txt**

Once you create an application on Twitch, go to its manage page and create a new secret. Copy that secret into this file.


### For Recorded Youtube Livestreams:
**YoutubeApiKey.txt**
You need to create a Google Cloud Platform Project and then use the console to generate an API Key (https://console.developers.google.com/apis/credentials). Once you have done this, you will also need to enable the Youtube Data API in the project to make requests (https://console.cloud.google.com/marketplace/product/google/youtube.googleapis.com)


## Usage
<code>python main.py [EventKey] [-t <Twitch_Vod_Ids>] [-y <Youtube_Video_Ids>]</code>

**Event_Key:** The event key on TheBlueAlliance (e.g. The 2019 Ventura Event is 2019cave)
**Twitch_Vod_Ids:** The ID of the vod from Twitch. If you navigate to the vod, its in the url like this: https://www.twitch.tv/videos/[VOD_ID]. You can put multiple vods at the end separated by a space when an event has multiple vods.
**Youtube_Video_Ids:** The ID of the video from Youtube. If you navigate to the vod, its in the url like this: https://www.youtube.com/watch?v=[VIDEO_ID]. You can put multiple videos at the end separated by a comma without spaces when an event has multiple videos.
  
**Examples:**

<code>python main.py 2017txwo -y DvVziU9WqCc</code>
  
This will attempt to generate Youtube URLs with the appropriate timestamps of the 2017 Lone Star North Regional matches from the Youtube Livestream recording https://www.youtube.com/watch?v=DvVziU9WqCc
  
<code>python main.py 2021txcls -t 1057112576,1057949790,1058960481,1059021401</code>

This will attempt to generate Twitch URLs with the appropriate timestamps of the 2021 Texas Cup - Lone Star Division matches using the Twitch Vods with the IDs 1057112576, 1057949790, 1058960481, 1059021401

  
## Output
The output will be a csv file titled [EventKey]\_vodTimestamps.csv. This will have 3 rows of data in the following order: matchKey, timestampType, vodUrl.

**matchKey:** The key for the match in the format of [EventKey]\_[MatchID] (e.g. 2021txcls_qm1 is Qualifcation Match 1 of the 2021 Texas Cup)

**timestampType:** Tells you which timestamp the generated url uses, either the actual match time or the scheduled match time

**vodUrl:** The URL to access the vod
