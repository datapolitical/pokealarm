# Standard Library Imports
import requests

# 3rd Party Imports

# Local Imports
from PokeAlarm.Alarms import Alarm
from PokeAlarm.Utils import parse_boolean, get_static_map_url, \
    reject_leftover_parameters, require_and_remove_key, get_image_url

try_sending = Alarm.try_sending
replace = Alarm.replace

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ATTENTION! !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#             ONLY EDIT THIS FILE IF YOU KNOW WHAT YOU ARE DOING!
# You DO NOT NEED to edit this file to customize messages! Please ONLY EDIT the
#     the 'alarms.json'. Failing to do so can cause other feature to break!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ATTENTION! !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


class DiscordAlarm(Alarm):

    _defaults = {
        'monsters': {
            'username': "<mon_name>",
            'content': "",
            'icon_url': get_image_url(
                "regular/monsters/<mon_id_3>_<form_id_3>.png"),
            'avatar_url': get_image_url(
                "regular/monsters/<mon_id_3>_<form_id_3>.png"),
            'display_icon_url': get_image_url(
                "regular/monsters/<display_mon_id_3>_<display_form_id_3>.png"),
            'display_avatar_url': get_image_url(
                "regular/monsters/<display_mon_id_3>_<display_form_id_3>.png"),
            'title': "A wild <mon_name> has appeared!",
            'url': "<gmaps>",
            'body': "Available until <24h_time> (<time_left>).",
            'footer_timestamp': '<disappear_time_utc>'
        },
        'stops': {
            'username': "Pokestop",
            'content': "",
            'icon_url': get_image_url("regular/stop/<lure_type_id_3>.png"),
            'avatar_url': get_image_url("regular/stop/<lure_type_id_3>.png"),
            'title': "Someone has placed a lure on a Pokestop!",
            'url': "<gmaps>",
            'body': "Lure will expire at <24h_time> (<time_left>).",
            'footer_timestamp': '<expiration_utc>'
        },
        'gyms': {
            'username': "<new_team> Gym Alerts",
            'content': "",
            'icon_url': get_image_url("regular/gyms/<new_team_id>.png"),
            'avatar_url': get_image_url("regular/gyms/<new_team_id>.png"),
            'title': "A Team <old_team> gym has fallen!",
            'url': "<gmaps>",
            'body': "It is now controlled by <new_team>."
        },
        'eggs': {
            'username': "Egg",
            'content': "",
            'icon_url': get_image_url("regular/eggs/<egg_lvl>.png"),
            'avatar_url': get_image_url("regular/eggs/<egg_lvl>.png"),
            'title': "Raid is incoming!",
            'url': "<gmaps>",
            'body': "A level <egg_lvl> raid will hatch at "
                    "<24h_hatch_time> (<hatch_time_left>).",
            'footer_timestamp': '<hatch_time_utc>'
        },
        'raids': {
            'username': "Raid",
            'content': "",
            'icon_url':
                get_image_url("regular/monsters/<mon_id_3>_<form_id_3>.png"),
            'avatar_url':
                get_image_url("regular/monsters/<mon_id_3>_<form_id_3>.png"),
            'title': "Level <raid_lvl> raid is available against <mon_name>!",
            'url': "<gmaps>",
            'body': "The raid is available until "
                    "<24h_raid_end> (<raid_time_left>).",
            'footer_timestamp': '<raid_end_utc>'
        },
        'weather': {
            'username': "Weather",
            'content': "",
            "icon_url": get_image_url("regular/weather/<weather_id_3>"
                                      "_<day_or_night_id_3>.png"),
            "avatar_url": get_image_url("regular/weather/<weather_id_3>"
                                        "_<day_or_night_id_3>.png"),
            "title": "The weather has changed!",
            "url": "<gmaps>",
            "body": "The weather around <lat>,<lng> has changed to <weather>!"
        },
        'quests': {
            'username': "Quest",
            'content': "",
            'icon_url': get_image_url("regular/<quest_image>.png"),
            'avatar_url': get_image_url("regular/<quest_image>.png"),
            'title': "New Quest Found!",
            'url': "<gmaps>",
            'body': "Do this: <quest_task>\nFor this: <reward>"
        },
        'invasions': {
            'username': "Invasion",
            'content': "",
            'icon_url':
                get_image_url("regular/invasions/<grunt_id_3>.png"),
            'avatar_url':
                get_image_url("regular/invasions/<grunt_id_3>.png"),
            'title': "This Pokestop has been invaded by Team Rocket!",
            'url': "<gmaps>",
            'body': "Invasion will expire at <24h_time> (<time_left>).",
            'footer_timestamp': '<expiration_utc>'
        }
    }

    # Gather settings and create alarm
    def __init__(self, mgr, settings, max_attempts, static_map_key):
        self._log = mgr.get_child_logger("alarms")
        # Required Parameters
        self.__webhook_url = require_and_remove_key(
            'webhook_url', settings, "'Discord' type alarms.")
        self.__max_attempts = max_attempts

        # Optional Alarm Parameters
        self.__startup_message = parse_boolean(
            settings.pop('startup_message', "True"))
        self.__startup_text = settings.pop('startup_text', "")
        self.__disable_embed = parse_boolean(
            settings.pop('disable_embed', "False"))
        self.__avatar_url = settings.pop('avatar_url', "")
        self.__map = settings.pop('map', {})
        self.__static_map_key = static_map_key
        self.__timestamp = settings.pop('footer_timestamp', False)

        # Set Alert Parameters
        self.__monsters = self.create_alert_settings(
            settings.pop('monsters', {}), self._defaults['monsters'])
        self.__stops = self.create_alert_settings(
            settings.pop('stops', {}), self._defaults['stops'])
        self.__gyms = self.create_alert_settings(
            settings.pop('gyms', {}), self._defaults['gyms'])
        self.__eggs = self.create_alert_settings(
            settings.pop('eggs', {}), self._defaults['eggs'])
        self.__raids = self.create_alert_settings(
            settings.pop('raids', {}), self._defaults['raids'])
        self.__weather = self.create_alert_settings(
            settings.pop('weather', {}), self._defaults['weather'])
        self.__quests = self.create_alert_settings(
            settings.pop('quests', {}), self._defaults['quests'])
        self.__invasions = self.create_alert_settings(
            settings.pop('invasions', {}), self._defaults['invasions'])

        # Warn user about leftover parameters
        reject_leftover_parameters(settings, "'Alarm level in Discord alarm.")

        self._log.info("Discord Alarm has been created!")

    # (Re)connect with Discord
    def connect(self):
        pass

    # Send a message letting the channel know that this alarm has started
    def startup_message(self):
        if self.__startup_message:
            args = {
                'url': self.__webhook_url,
                'payload': {
                    'username': 'PokeAlarm',
                    'content': ('PokeAlarm activated!'
                                if self.__startup_text == ""
                                else self.__startup_text)
                }
            }
            try_sending(self._log, self.connect, "Discord",
                        self.send_webhook, args, self.__max_attempts)
            self._log.info("Startup message sent!")

    # Set the appropriate settings for each alert
    def create_alert_settings(self, settings, default):
        map = settings.pop('map', self.__map)
        use_display_icon = settings.pop('use_display_icon', False)
        use_display_avatar = settings.pop('use_display_avatar', False)

        alert = {
            'webhook_url': settings.pop('webhook_url', self.__webhook_url),
            'username': settings.pop('username', default['username']),
            'avatar_url': settings.pop(
                'avatar_url',
                default['display_avatar_url']
                if use_display_avatar else default['avatar_url']),
            'disable_embed': parse_boolean(
                settings.pop('disable_embed', self.__disable_embed)),
            'content': settings.pop('content', default['content']),
            'icon_url': settings.pop(
                'icon_url',
                default['display_icon_url']
                if use_display_icon else default['icon_url']),
            'title': settings.pop('title', default['title']),
            'url': settings.pop('url', default['url']),
            'body': settings.pop('body', default['body']),
            'fields': settings.pop('fields', []),
            'map': map if isinstance(map, str) else
            get_static_map_url(map, self.__static_map_key)
        }

        timestamp = settings.pop('footer_timestamp', self.__timestamp)
        if isinstance(timestamp, str):
            alert['timestamp'] = timestamp
        if timestamp is True and 'footer_timestamp' in default:
            alert['timestamp'] = default['footer_timestamp']

        reject_leftover_parameters(settings, "'Alert level in Discord alarm.")
        return alert

    # Send Alert to Discord
    def send_alert(self, alert, info):
        self._log.debug("Attempting to send notification to Discord.")
        payload = {
            # Usernames are limited to 32 characters
            'username': replace(alert['username'], info)[:32],
            'content': replace(alert['content'], info),
            'avatar_url': replace(alert['avatar_url'], info),
        }
        if alert['disable_embed'] is False:
            payload['embeds'] = [{
                'title': replace(alert['title'], info),
                'url': replace(alert['url'], info),
                'description': replace(alert['body'], info),
                'thumbnail': {'url': replace(alert['icon_url'], info)},
                'fields': self.replace_fields(alert['fields'], info)
            }]

            if alert['map'] is not None:
                coords = {
                    'lat': info['lat'],
                    'lng': info['lng']
                }
                payload['embeds'][0]['image'] = {
                    'url':
                        replace(alert['map'],
                                coords if not
                                isinstance(alert['map'], str)
                                else info)
                }

            if 'timestamp' in alert:
                payload['embeds'][0]['timestamp'] = replace(
                    alert['timestamp'], info)
        args = {
            'url': replace(alert['webhook_url'], info),
            'payload': payload
        }

        try_sending(self._log, self.connect,
                    "Discord", self.send_webhook, args, self.__max_attempts)

    # Trigger an alert based on Pokemon info
    def pokemon_alert(self, pokemon_info):
        self._log.debug("Pokemon notification triggered.")
        self.send_alert(self.__monsters, pokemon_info)

    # Trigger an alert based on Pokestop info
    def pokestop_alert(self, pokestop_info):
        self._log.debug("Pokestop notification triggered.")
        self.send_alert(self.__stops, pokestop_info)

    # Trigger an alert based on Pokestop info
    def gym_alert(self, gym_info):
        self._log.debug("Gym notification triggered.")
        self.send_alert(self.__gyms, gym_info)

    # Trigger an alert when a raid egg has spawned (UPCOMING raid event)
    def raid_egg_alert(self, raid_info):
        self._log.debug("Raid Egg notification triggered.")
        self.send_alert(self.__eggs, raid_info)

    def raid_alert(self, raid_info):
        self._log.debug("Raid notification triggered.")
        self.send_alert(self.__raids, raid_info)

    # Trigger an alert based on Weather info
    def weather_alert(self, weather_info):
        self._log.debug("Weather notification triggered.")
        self.send_alert(self.__weather, weather_info)

    def quest_alert(self, quest_info):
        self._log.debug("Quest notification triggered.")
        self.send_alert(self.__quests, quest_info)

    def invasion_alert(self, invasion_info):
        self._log.debug("Invasion notification triggered.")
        self.send_alert(self.__invasions, invasion_info)

    # Send a payload to the webhook url
    def send_webhook(self, url, payload):
        self._log.debug(payload)
        resp = requests.post(url, json=payload, timeout=5)
        if resp.ok is True:
            self._log.debug("Notification successful (returned {})".format(
                resp.status_code))
        else:
            self._log.debug("Discord response was {}".format(resp.content))
            raise requests.exceptions.RequestException(
                "Response received {}, webhook not accepted.".format(
                    resp.status_code))

    @staticmethod
    def replace_fields(fields, pkinfo):
        replaced_fields = []
        for field in fields:
            replaced_fields.append({
                'name': replace(field['name'], pkinfo),
                'value': replace(field['value'], pkinfo),
                'inline': field.get('inline', False)
            })
        return replaced_fields
