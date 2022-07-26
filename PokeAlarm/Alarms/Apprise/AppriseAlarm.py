# Standard Library Imports
import re
from datetime import datetime

import apprise

# Create an Apprise instance
apobj = apprise.Apprise()
apobj.add('pover://upnf42igs2yetr5s6se6swqu6qwibq@apks9w8g1vmm3wepa8fyrt5dhejc4n')

# Local Imports
from PokeAlarm.Alarms import Alarm
from PokeAlarm.Utils import parse_boolean, get_static_map_url, get_time_as_str, \
    require_and_remove_key, reject_leftover_parameters, get_image_url

try_sending = Alarm.try_sending
replace = Alarm.replace
url_regex = re.compile(
    r"(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]"
    r"@!\$&'\(\)\*\+,;=.]+", re.I)


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ATTENTION! !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#             ONLY EDIT THIS FILE IF YOU KNOW WHAT YOU ARE DOING!
# You DO NOT NEED to edit this file to customize messages! Please ONLY EDIT the
#     the 'alarms.json'. Failing to do so can cause other feature to break!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ATTENTION! !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


class AppriseAlarm(Alarm):

    _defaults = {
        'monsters': {
            'status':"A wild <mon_name> has appeared! Available until <24h_time> (<time_left>). <gmaps>",
            'map':{
                'width':"250",
                'height':"125",
                'maptype':"roadmap",
                'zoom':"15"
            },
            'title':"Pokemon Alert!",
            'url':"<gmaps>"
        },
        'stops': {
            'status': "Someone has placed a lure on a Pokestop! "
                      "Lure will expire at <24h_time> (<time_left>). <gmaps>",
            'title':"Pokemon Alert!",
            'url':"<gmaps>"
        },
        'gyms': {
            'status': "A Team <old_team> gym has fallen! "
                      "It is now controlled by <new_team>. <gmaps>",
            'title':"Gym Alert!",
            'url':"<gmaps>"
        },
        'eggs': {
            'status': "Level <egg_lvl> raid incoming! Hatches at "
                      "<24h_hatch_time> (<hatch_time_left>). <gmaps>",
            'title':"Egg Alert!",
            'url':"<gmaps>"
        },
        'raids': {
            'status': "Raid <raid_lvl> against <mon_name>! Available until "
                      "<24h_raid_end> (<raid_time_left>). <gmaps>",
            'title':"Raid Alert!",
            'url':"<gmaps>"
        },
        'weather': {
            'status': "The weather around <lat>,<lng> has changed"
                      " to <weather>!",
            'title':"Weather Alert!",
            'url':"<gmaps>"
        },
        'quests': {
            'status': "*New quest for <reward>*\n<quest_task>\n<gmaps>",
            'title':"Quest Alert!",
            'url':"<gmaps>"
        },
        "invasions": {
            'status': "A Pokestop has been invaded by Team Rocket!\n"
                      "Invasion will expire at <24h_time> (<time_left>).",
            'title':"Invasion Alert!",
            'url':"<gmaps>"
        }
    }

    # Gather settings and create alarm
    def __init__(self, mgr, settings, static_map_key):
        self._log = mgr.get_child_logger("alarms")


        # Optional Alarm Parameters
        self.__startup_message = parse_boolean(
            settings.pop('startup_message', "True"))
        self.__startup_text = settings.pop('startup_text', "")
        self.__map = settings.pop('map', {})
        self.__static_map_key = static_map_key

        # Optional Alert Parameters
        self.__pokemon = self.create_alert_settings(
            settings.pop('monsters', {}), self._defaults['monsters'])
        self.__pokestop = self.create_alert_settings(
            settings.pop('stops', {}), self._defaults['stops'])
        self.__gym = self.create_alert_settings(
            settings.pop('gyms', {}), self._defaults['gyms'])
        self.__egg = self.create_alert_settings(
            settings.pop('eggs', {}), self._defaults['eggs'])
        self.__raid = self.create_alert_settings(
            settings.pop('raids', {}), self._defaults['raids'])
        self.__weather = self.create_alert_settings(
            settings.pop('weather', {}), self._defaults['weather'])
        self.__quest = self.create_alert_settings(
            settings.pop('quests', {}), self._defaults['quests'])
        self.__invasion = self.create_alert_settings(
            settings.pop('invasions', {}), self._defaults['invasions'])

        # Warn user about leftover parameters
        reject_leftover_parameters(settings, "'Alarm level in Twitter alarm.")

        self._log.info("Twitter Alarm has been created!")

    # Establish connection with Twitter
    def connect(self):
        print("skippingTwitter")

    # Send a start up tweet
    def startup_message(self):
        if self.__startup_message:
            print("not doing this")

    # Set the appropriate settings for each alert
    def create_alert_settings(self, settings, default):
        map = settings.pop('map', self.__map)
        use_display_icon = settings.pop('use_display_icon', False)
        alert = {
            'title': settings.pop('title', default['title']),
            'url': settings.pop('url', default['url']),
            'status': settings.pop('status', default['status']),
            'map': map if isinstance(map, str) else
            get_static_map_url(map, self.__static_map_key)
        }
        reject_leftover_parameters(settings, "'Alert level in Twitter alarm.")
        return alert

    # Shortens the tweet down, calculating for urls being shortened
    def shorten(self, message, limit=280, url_length=23):
        msg = ""
        for word in re.split(r'\s', message):
            word_len = len(word)
            if url_regex.match(word):  # If it's a url
                if limit <= url_length:  # if the whole thing doesn't fit
                    break  # Don't add the url
                word_len = url_length  # URL's have a fixed length
            elif word_len >= limit:  # If the word doesn't fit
                word_len = limit - 1
                word = word[:word_len]  # truncate it
            limit -= word_len + 1  # word + space
            msg += " " + word
        print(msg)
        return msg[1:]  # Strip the space

    def send_alert(self, alert, info):
        coords = {
            'lat': info['lat'],
            'lng': info['lng']
        }
        attachments = [{
            'fallback': 'Map_Preview',
            'image_url':
                replace(alert['map'],
                        info if isinstance(map, str) else coords)
        }] if alert['map'] is not None else None
        message = replace(alert['status'], info)
        url = replace(alert['url'], info)
        mapurl = replace(alert['map'], info)
        apobj.notify(body=message, title='Pokemon Notification!', attach=mapurl)

    # Trigger an alert based on Pokemon info
    def pokemon_alert(self, pokemon_info):
        self.send_alert(self.__pokemon, pokemon_info)

    # Trigger an alert based on Pokestop info
    def pokestop_alert(self, pokestop_info):
        self.send_alert(self.__pokestop, pokestop_info)

    # Trigger an alert based on Gym info
    def gym_alert(self, gym_info):
        self.send_alert(self.__gym, gym_info)

    # Trigger an alert when a raid egg has spawned (UPCOMING raid event)
    def raid_egg_alert(self, raid_info):
        self.send_alert(self.__egg, raid_info)

    # Trigger an alert based on Gym info
    def raid_alert(self, raid_info):
        self.send_alert(self.__raid, raid_info)

    # Trigger an alert based on weather webhook
    def weather_alert(self, weather_info):
        self.send_alert(self.__weather, weather_info)

    # Trigger an alert based on weather webhook
    def quest_alert(self, quest_info):
        self.send_alert(self.__quest, quest_info)

    # Trigger an alert based on invasion pokestop webhook
    def invasion_alert(self, invasion_info):
        self.send_alert(self.__invasion, invasion_info)

    # Send out a tweet with the given status
    def send_tweet(self, status):
        self.__client.statuses.update(status=status)
