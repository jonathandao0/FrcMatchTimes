# FrcMatchTimes

Tool to get timestamps for matches from Twitch Vods to view. This tries to match the match time taken from TheBlueAlliance to generate the appropriate twitch.tv vod URL to watch the match given the provided Twitch vod IDs. This tries to use the actual match time if it is given and falls back to the scheduled match time if no actual match time is given. Note that if the url is generated using the scheduled match time, it will most likely be off. 

Note that this will be limited for events older than 2019 as FRC events weren't really broadcasted through Twitch prior to the 2019 season.

## Requirements:
You need to create 3 text files in the base directory with their appropriate keys. Note that these should be kept private to avoid potential abuse:

**TbaApiKey.txt**

Obtained by creating an account on TheBlueAlliance and accessing your account page (https://www.thebluealliance.com/account). Generate a Read API Key and put it in this file.

**TwitchClientId.txt**

Obtained by creating an application on Twitch (https://dev.twitch.tv/console/apps). Copy the Client ID into this file.

**TwitchClientSecret.txt**

Once you create an application on Twitch, go to its manage page and create a new secret. Copy that secret into this file.

## Usage
<code>main.py [EventKey] [Twitch_Vod_Ids]...</code>

**Event_Key:** The event key on TheBlueAlliance (e.g. The 2019 Ventura Event is 2019cave)
**Twitch_Vod_Ids:** The ID of the vod from twitch. If you navigate to the vod, its in the url like this: https://www.twitch.tv/videos/[VOD_ID]. You can put multiple vods at the end separated by a space when an event has them split up.

Example:

<code>main.py 2021txcls 1057112576 1057949790 1058960481 1059021401</code>

This will attempt to match all of the 2021 Texas Cup - Lone Star Division matches with the start time of the matches using the Twitch Vods with the IDs 1057112576, 1057949790, 1058960481, 1059021401


## Output
The output will be a csv file titled [EventKey]\_vodTimestamps.csv. This will have 3 rows of data in the following order: matchKey, timestampType, vodUrl.

**matchKey:** The key for the match in the format of [EventKey]\_[MatchID] (e.g. 2021txcls_qm1 is Qualifcation Match 1 of the 2021 Texas Cup)

**timestampType:** Tells you which timestamp the generated url uses, either the actual match time or the scheduled match time

**vodUrl:** The URL to access the vod
