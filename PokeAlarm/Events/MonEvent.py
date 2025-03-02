# Standard Library Imports
import re
from datetime import datetime
from urllib.parse import urlencode
# 3rd Party Imports
# Local Imports
from PokeAlarm import Unknown
from PokeAlarm.Utilities import PvpUtils
from PokeAlarm.Utils import (
    get_gmaps_link, get_move_type, get_move_damage, get_move_dps,
    get_move_duration, get_move_energy, get_pokemon_size,
    get_applemaps_link, get_shiny_emoji, get_time_as_str,
    get_seconds_remaining, get_base_types, get_dist_as_str,
    get_weather_emoji, get_spawn_verified_emoji, get_type_emoji,
    get_waze_link, get_gender_sym, is_weather_boosted,
    get_cached_weather_id_from_coord)
from . import BaseEvent
from PokeAlarm.Utilities import MonUtils


class MonEvent(BaseEvent):
    """ Event representing the discovery of a Pokemon. """

    def __init__(self, data):
        """ Creates a new Monster Event based on the given dict. """
        super(MonEvent, self).__init__('monster')
        check_for_none = BaseEvent.check_for_none

        # Identification
        self.enc_id = data['encounter_id']
        self.monster_id = int(data['pokemon_id'])
        self.form_id = check_for_none(int, data.get('form'), 0)

        # Time Left
        self.disappear_time = datetime.utcfromtimestamp(data['disappear_time'])
        self.time_left = get_seconds_remaining(self.disappear_time)

        # Spawn Data
        self.spawn_start = check_for_none(
            int, data.get('spawn_start'), Unknown.REGULAR)
        self.spawn_end = check_for_none(
            int, data.get('spawn_end'), Unknown.REGULAR)
        self.spawn_verified = check_for_none(
            int,
            data.get('verified', data.get('disappear_time_verified')),
            Unknown.REGULAR)
        self.spawnpoint_id = check_for_none(
            str, data.get('spawnpoint_id'), Unknown.REGULAR)

        # Location
        self.lat = float(data['latitude'])
        self.lng = float(data['longitude'])
        self.distance = Unknown.SMALL  # Completed by Manager
        self.direction = Unknown.TINY  # Completed by Manager

        # Weather Infos
        self.weather_id = check_for_none(
            int, data.get('weather'), Unknown.TINY)
        self.boosted_weather_id = \
            0 if Unknown.is_not(self.weather_id) else Unknown.TINY
        if is_weather_boosted(self.weather_id, self.monster_id, self.form_id):
            self.boosted_weather_id = self.weather_id

        # Encounter Stats
        self.mon_lvl = check_for_none(
            int, data.get('pokemon_level'), Unknown.TINY)
        self.cp = check_for_none(int, data.get('cp'), Unknown.TINY)

        # IVs
        self.atk_iv = check_for_none(
            int, data.get('individual_attack'), Unknown.TINY)
        self.def_iv = check_for_none(
            int, data.get('individual_defense'), Unknown.TINY)
        self.sta_iv = check_for_none(
            int, data.get('individual_stamina'), Unknown.TINY)
        if Unknown.is_not(self.atk_iv, self.def_iv, self.sta_iv):
            self.iv = \
                100 * (self.atk_iv + self.def_iv + self.sta_iv) / float(45)
            (self.great_product, self.great_id, self.great_cp,
             self.great_level, self.great_candy, self.great_stardust,
             self.ultra_product, self.ultra_id, self.ultra_cp,
             self.ultra_level, self.ultra_candy, self.ultra_stardust) = \
                PvpUtils.get_pvp_info(
                    self.monster_id, self.form_id, self.atk_iv, self.def_iv,
                    self.sta_iv, self.mon_lvl)
        else:
            self.iv = Unknown.SMALL
            self.great_product = Unknown.SMALL
            self.ultra_product = Unknown.SMALL
            self.great_id = self.monster_id
            self.ultra_id = self.monster_id
            self.great_cp = Unknown.SMALL
            self.ultra_cp = Unknown.SMALL
            self.great_level = Unknown.SMALL
            self.ultra_level = Unknown.SMALL
            self.great_candy = Unknown.SMALL
            self.ultra_candy = Unknown.SMALL
            self.great_stardust = Unknown.SMALL
            self.ultra_stardust = Unknown.SMALL

        # Quick Move
        self.quick_id = check_for_none(
            int, data.get('move_1'), Unknown.TINY)
        self.quick_type = get_move_type(self.quick_id)
        self.quick_damage = get_move_damage(self.quick_id)
        self.quick_dps = get_move_dps(self.quick_id)
        self.quick_duration = get_move_duration(self.quick_id)
        self.quick_energy = get_move_energy(self.quick_id)

        # Charge Move
        self.charge_id = check_for_none(
            int, data.get('move_2'), Unknown.TINY)
        self.charge_type = get_move_type(self.charge_id)
        self.charge_damage = get_move_damage(self.charge_id)
        self.charge_dps = get_move_dps(self.charge_id)
        self.charge_duration = get_move_duration(self.charge_id)
        self.charge_energy = get_move_energy(self.charge_id)

        # Catch Probs
        self.base_catch = check_for_none(
            float,
            data.get('base_catch', data.get('capture_1')),
            Unknown.TINY)
        self.great_catch = check_for_none(
            float,
            data.get('great_catch', data.get('capture_2')),
            Unknown.TINY)
        self.ultra_catch = check_for_none(
            float,
            data.get('ultra_catch', data.get('capture_3')),
            Unknown.TINY)

        # Attack Rating
        self.atk_grade = check_for_none(
            str, data.get('atk_grade'), Unknown.TINY)
        self.def_grade = check_for_none(
            str, data.get('def_grade'), Unknown.TINY)

        # Cosmetic
        self.gender = get_gender_sym(
            check_for_none(int, data.get('gender'), Unknown.TINY))
        self.height = check_for_none(float, data.get('height'), Unknown.SMALL)
        self.weight = check_for_none(float, data.get('weight'), Unknown.SMALL)
        if Unknown.is_not(self.height, self.weight):
            self.size_id = get_pokemon_size(
                self.monster_id, self.height, self.weight)
        else:
            self.size_id = Unknown.SMALL

        self.types = get_base_types(self.monster_id, self.form_id)
        self.can_be_shiny = MonUtils.get_shiny_status(
            self.monster_id, self.form_id)

        # Costume
        self.costume_id = check_for_none(int, data.get('costume'), 0)

        # Rarity
        self.rarity_id = check_for_none(int, data.get('rarity'), Unknown.TINY)

        # Display Monster Information (Generally the real monster is ditto)
        self.display_monster_id = check_for_none(
            int, data.get('display_pokemon_id'), 0)
        self.display_form_id = check_for_none(
            int, data.get('display_form'), 0)
        self.display_costume_id = check_for_none(
            int, data.get('display_costume'), 0)
        self.display_gender = get_gender_sym(
            check_for_none(int, data.get('display_gender'), Unknown.TINY))

        # Correct this later
        self.name = self.monster_id
        self.geofence = Unknown.REGULAR
        self.custom_dts = {}

    def update_with_cache(self, cache):
        """ Update event infos using cached data from previous events. """

        # Update weather
        weather_id = get_cached_weather_id_from_coord(
            self.lat, self.lng, cache)
        if Unknown.is_not(weather_id):
            self.weather_id = BaseEvent.check_for_none(
                int, weather_id, Unknown.TINY)
            self.boosted_weather_id = \
                0 if Unknown.is_not(self.weather_id) else Unknown.TINY
            if is_weather_boosted(self.weather_id, self.monster_id,
                                  self.form_id):
                self.boosted_weather_id = self.weather_id

    def generate_dts(self, locale, timezone, units):
        """ Return a dict with all the DTS for this event. """
        time = get_time_as_str(self.disappear_time, timezone)

        form_name = locale.get_form_name(self.monster_id, self.form_id)
        costume_name = locale.get_costume_name(
            self.monster_id, self.costume_id)

        weather_name = locale.get_weather_name(self.weather_id)
        boosted_weather_name = locale.get_weather_name(self.boosted_weather_id)

        type1 = locale.get_type_name(self.types[0])
        type2 = locale.get_type_name(self.types[1])

        dts = self.custom_dts.copy()
        dts.update({
            # Identification
            'encounter_id': self.enc_id,
            'mon_name': locale.get_pokemon_name(self.monster_id),
            'mon_id': self.monster_id,
            'mon_id_3': "{:03}".format(self.monster_id),

            # Time Remaining
            'time_left': time[0],
            '12h_time': time[1],
            '24h_time': time[2],
            'time_left_no_secs': time[3],
            '12h_time_no_secs': time[4],
            '24h_time_no_secs': time[5],
            'time_left_raw_hours': time[6],
            'time_left_raw_minutes': time[7],
            'time_left_raw_seconds': time[8],
            'disappear_time_utc': self.disappear_time,
            'current_timestamp_utc': datetime.utcnow(),

            # Spawn Data
            'spawn_start': self.spawn_start,
            'spawn_end': self.spawn_end,
            'spawn_verified':
                self.spawn_verified > 0 if Unknown.is_not(self.spawn_verified)
                else Unknown.REGULAR,
            'spawn_verified_emoji': get_spawn_verified_emoji(
                self.spawn_verified),
            'spawn_verified_emoji_or_empty': (
                '' if self.spawn_verified != 1
                else get_spawn_verified_emoji(self.spawn_verified)),
            'spawn_unverified_emoji_or_empty': (
                '' if self.spawn_verified != 0
                else get_spawn_verified_emoji(self.spawn_verified)),
            'spawnpoint_id': self.spawnpoint_id,

            # Location
            'lat': self.lat,
            'lng': self.lng,
            'lat_5': "{:.5f}".format(self.lat),
            'lng_5': "{:.5f}".format(self.lng),
            'distance': (
                get_dist_as_str(self.distance, units)
                if Unknown.is_not(self.distance) else Unknown.SMALL),
            'direction': self.direction,
            'gmaps': get_gmaps_link(self.lat, self.lng, False),
            'gnav': get_gmaps_link(self.lat, self.lng, True),
            'applemaps': get_applemaps_link(self.lat, self.lng, False),
            'applenav': get_applemaps_link(self.lat, self.lng, True),
            'waze': get_waze_link(self.lat, self.lng, False),
            'wazenav': get_waze_link(self.lat, self.lng, True),
            'geofence': self.geofence,

            # Weather
            'weather_id': self.weather_id,
            'weather': weather_name,
            'weather_or_empty': Unknown.or_empty(weather_name),
            'weather_emoji': get_weather_emoji(self.weather_id),
            'boosted_weather_id': self.boosted_weather_id,
            'boosted_weather': boosted_weather_name,
            'boosted_weather_or_empty': (
                '' if self.boosted_weather_id == 0
                else Unknown.or_empty(boosted_weather_name)),
            'boosted_weather_emoji':
                get_weather_emoji(self.boosted_weather_id),
            'boosted_or_empty': locale.get_boosted_text() if \
                Unknown.is_not(self.boosted_weather_id) and
                self.boosted_weather_id != 0 else '',

            # Encounter Stats
            'mon_lvl': self.mon_lvl,
            'cp': self.cp,

            # IVs
            'iv_0': (
                "{:.0f}".format(self.iv) if Unknown.is_not(self.iv)
                else Unknown.TINY),
            'iv': (
                "{:.1f}".format(self.iv) if Unknown.is_not(self.iv)
                else Unknown.SMALL),
            'iv_2': (
                "{:.2f}".format(self.iv) if Unknown.is_not(self.iv)
                else Unknown.SMALL),
            'atk': self.atk_iv,
            'def': self.def_iv,
            'sta': self.sta_iv,

            # PVP Information
            'great_mon_id': self.great_id,
            'great_product': self.great_product,
            'great_mon_name': locale.get_pokemon_name(self.great_id),
            'great_cp': self.great_cp,
            'great_level': self.great_level,
            'great_url': 'https://www.stadiumgaming.gg/rank-checker?'
                + urlencode({
                    'pokemon': re.sub(r'[^A-Za-z0-9\s]+', '',
                                      locale.get_english_pokemon_name(
                                          self.great_id)),
                    'league': '1500',
                    'att_iv': '"{}"'.format(self.atk_iv),
                    'def_iv': '"{}"'.format(self.def_iv),
                    'hp_iv': '"{}"'.format(self.sta_iv),
                    'min-iv': '0',
                    'levelCap': '50'
                }),
            'great_pvpoke':
                'https://{}/rankings/all/1500/overall/{}{}/'.format(
                    locale.get_pvpoke_domain(),
                    re.sub(r'[^A-Za-z0-9\s]+', '',
                           locale.get_english_pokemon_name(self.great_id))
                    .lower().replace(' ', '_'),
                    '_' + re.sub(r'[^A-Za-z0-9\s]+', '',
                                 locale.get_english_form_name(
                                     self.great_id, self.form_id)
                                 .lower().replace(' ', '_'))
                    if not any(x in locale.get_english_form_name(
                        self.great_id, self.form_id)
                        for x in ['unknown', 'Normal'])
                    else ''),
            'great_candy': self.great_candy,
            'great_stardust': self.great_stardust,
            'ultra_mon_id': self.ultra_id,
            'ultra_product': self.ultra_product,
            'ultra_mon_name': locale.get_pokemon_name(self.ultra_id),
            'ultra_cp': self.ultra_cp,
            'ultra_level': self.ultra_level,
            'ultra_url': 'https://www.stadiumgaming.gg/rank-checker?'
                + urlencode({
                    'pokemon': re.sub(r'[^A-Za-z0-9\s]+', '',
                                      locale.get_english_pokemon_name(
                                          self.ultra_id)),
                    'league': '2500',
                    'att_iv': '"{}"'.format(self.atk_iv),
                    'def_iv': '"{}"'.format(self.def_iv),
                    'hp_iv': '"{}"'.format(self.sta_iv),
                    'min-iv': '0',
                    'levelCap': '50'
                }),
            'ultra_pvpoke':
                'https://{}/rankings/all/2500/overall/{}{}/'.format(
                    locale.get_pvpoke_domain(),
                    re.sub(r'[^A-Za-z0-9\s]+', '',
                           locale.get_english_pokemon_name(self.ultra_id))
                    .lower().replace(' ', '_'),
                    '_' + re.sub(r'[^A-Za-z0-9\s]+', '',
                                 locale.get_english_form_name(
                                     self.ultra_id, self.form_id)
                                 .lower().replace(' ', '_'))
                    if not any(x in locale.get_english_form_name(
                        self.ultra_id, self.form_id)
                        for x in ['unknown', 'Normal'])
                    else ''),
            'ultra_candy': self.ultra_candy,
            'ultra_stardust': self.ultra_stardust,
            # Type
            'type1': type1,
            'type1_or_empty': Unknown.or_empty(type1),
            'type1_emoji': Unknown.or_empty(get_type_emoji(self.types[0])),
            'type2': type2,
            'type2_or_empty': Unknown.or_empty(type2),
            'type2_emoji': Unknown.or_empty(get_type_emoji(self.types[1])),
            'types': (
                "{}/{}".format(type1, type2)
                if Unknown.is_not(type2) else type1),
            'types_emoji': (
                "{}{}".format(
                    get_type_emoji(self.types[0]),
                    get_type_emoji(self.types[1]))
                if Unknown.is_not(type2) else get_type_emoji(self.types[0])),

            # Form
            'form': form_name,
            'form_or_empty': Unknown.or_empty(form_name),
            'nonnormal_form_or_empty': (
                '' if locale.get_english_form_name(
                    self.monster_id, self.form_id) == 'Normal'
                else Unknown.or_empty(form_name)),
            'form_id': self.form_id,
            'form_id_2': "{:02d}".format(self.form_id),
            'form_id_3': "{:03d}".format(self.form_id),

            # Costume
            'costume': costume_name,
            'costume_or_empty': Unknown.or_empty(costume_name),
            'costume_id': self.costume_id,
            'costume_id_2': "{:02d}".format(self.costume_id),
            'costume_id_3': "{:03d}".format(self.costume_id),

            # Quick Move
            'quick_move': locale.get_move_name(self.quick_id),
            'quick_id': self.quick_id,
            'quick_type_id': self.quick_type,
            'quick_type': locale.get_type_name(self.quick_type),
            'quick_type_emoji': get_type_emoji(self.quick_type),
            'quick_damage': self.quick_damage,
            'quick_dps': self.quick_dps,
            'quick_duration': self.quick_duration,
            'quick_energy': self.quick_energy,

            # Charge Move
            'charge_move': locale.get_move_name(self.charge_id),
            'charge_id': self.charge_id,
            'charge_type_id': self.charge_type,
            'charge_type': locale.get_type_name(self.charge_type),
            'charge_type_emoji': get_type_emoji(self.charge_type),
            'charge_damage': self.charge_damage,
            'charge_dps': self.charge_dps,
            'charge_duration': self.charge_duration,
            'charge_energy': self.charge_energy,

            # Cosmetic
            'gender': self.gender,
            'height_0': (
                "{:.0f}".format(self.height) if Unknown.is_not(self.height)
                else Unknown.TINY),
            'height': (
                "{:.1f}".format(self.height) if Unknown.is_not(self.height)
                else Unknown.SMALL),
            'height_2': (
                "{:.2f}".format(self.height) if Unknown.is_not(self.height)
                else Unknown.SMALL),
            'weight_0': (
                "{:.0f}".format(self.weight) if Unknown.is_not(self.weight)
                else Unknown.TINY),
            'weight': (
                "{:.1f}".format(self.weight) if Unknown.is_not(self.weight)
                else Unknown.SMALL),
            'weight_2': (
                "{:.2f}".format(self.weight) if Unknown.is_not(self.weight)
                else Unknown.SMALL),
            'size': locale.get_size_name(self.size_id),
            'shiny_emoji': get_shiny_emoji(self.can_be_shiny),

            # Display Information (Usually when the actual mon is a ditto)
            'display_mon_id': self.display_monster_id,
            'display_mon_name': locale.get_pokemon_name(
                self.display_monster_id),
            'display_mon_id_3': "{:03}".format(self.display_monster_id),
            'display_mon_id_2': "{:02}".format(self.display_monster_id),
            'display_costume_id': self.display_costume_id,
            'display_costume_id_2': "{:02d}".format(self.display_costume_id),
            'display_costume_id_3': "{:03d}".format(self.display_costume_id),
            'display_costume': locale.get_costume_name(
                self.display_monster_id, self.display_costume_id),
            'display_form_id': self.display_form_id,
            'display_form': locale.get_form_name(
                self.display_monster_id, self.display_form_id),
            'display_form_id_3': "{:03d}".format(self.display_form_id),
            'display_form_id_2': "{:02d}".format(self.display_form_id),
            'display_gender': self.display_gender,

            # Misc
            'atk_grade': (
                Unknown.or_empty(self.atk_grade, Unknown.TINY)),
            'def_grade': (
                Unknown.or_empty(self.def_grade, Unknown.TINY)),
            'rarity_id': self.rarity_id,
            'rarity': locale.get_rarity_name(self.rarity_id),

            # Catch Prob
            'base_catch_0': (
                "{:.0f}".format(self.base_catch * 100)
                if Unknown.is_not(self.base_catch)
                else Unknown.TINY),
            'base_catch': (
                "{:.1f}".format(self.base_catch * 100)
                if Unknown.is_not(self.base_catch)
                else Unknown.SMALL),
            'base_catch_2': (
                "{:.2f}".format(self.base_catch * 100)
                if Unknown.is_not(self.base_catch)
                else Unknown.SMALL),
            'great_catch_0': (
                "{:.0f}".format(self.great_catch * 100)
                if Unknown.is_not(self.great_catch)
                else Unknown.TINY),
            'great_catch': (
                "{:.1f}".format(self.great_catch * 100)
                if Unknown.is_not(self.great_catch)
                else Unknown.SMALL),
            'great_catch_2': (
                "{:.2f}".format(self.great_catch * 100)
                if Unknown.is_not(self.great_catch)
                else Unknown.SMALL),
            'ultra_catch_0': (
                "{:.0f}".format(self.ultra_catch * 100)
                if Unknown.is_not(self.ultra_catch)
                else Unknown.TINY),
            'ultra_catch': (
                "{:.1f}".format(self.ultra_catch * 100)
                if Unknown.is_not(self.ultra_catch)
                else Unknown.SMALL),
            'ultra_catch_2': (
                "{:.2f}".format(self.ultra_catch * 100)
                if Unknown.is_not(self.ultra_catch)
                else Unknown.SMALL),

            # Misc
            'big_karp': (
                'big' if self.monster_id == 129 and Unknown.is_not(self.weight)
                and self.weight >= 13.13 else ''),
            'tiny_rat': (
                'tiny' if self.monster_id == 19 and Unknown.is_not(self.weight)
                and self.weight <= 2.41 else '')
        })
        return dts
