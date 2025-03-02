# Standard Library Imports
from datetime import datetime
# 3rd Party Imports
# Local Imports
from PokeAlarm import Unknown
from . import BaseEvent
from PokeAlarm.Utils import get_gmaps_link, get_applemaps_link, \
    get_time_as_str, get_move_type, get_move_damage, get_move_dps, \
    get_move_duration, get_move_energy, get_seconds_remaining, \
    get_dist_as_str, get_pokemon_cp_range, is_weather_boosted, \
    get_base_types, get_weather_emoji, get_type_emoji, get_waze_link, \
    get_team_emoji, get_ex_eligible_emoji, get_shiny_emoji, \
    get_gender_sym, get_cached_weather_id_from_coord
from PokeAlarm.Utilities import MonUtils


class RaidEvent(BaseEvent):
    """ Event representing the discovery of a Raid. """

    def __init__(self, data):
        """ Creates a new Stop Event based on the given dict. """
        super(RaidEvent, self).__init__('raid')
        check_for_none = BaseEvent.check_for_none

        # Identification
        self.gym_id = data.get('gym_id')

        # Time Remaining
        self.raid_end = datetime.utcfromtimestamp(
            data.get('end') or data.get('raid_end'))  # RM or Monocle
        self.time_left = get_seconds_remaining(self.raid_end)

        # Location
        self.lat = float(data['latitude'])
        self.lng = float(data['longitude'])
        self.distance = Unknown.SMALL  # Completed by Manager
        self.direction = Unknown.TINY  # Completed by Manager

        # Monster Info
        self.raid_lvl = int(data['level'])
        self.mon_id = int(data['pokemon_id'])
        self.form_id = check_for_none(int, data.get('form'), 0)
        self.cp = int(data['cp'])
        self.types = get_base_types(self.mon_id, self.form_id)
        self.boss_level = 20
        self.gender = get_gender_sym(
            check_for_none(int, data.get('gender'), Unknown.TINY))
        self.can_be_shiny = MonUtils.get_shiny_status(
            self.mon_id, self.form_id)

        # Evolution
        self.evolution_id = check_for_none(int, data.get('evolution'), 0)

        # Costume
        self.costume_id = check_for_none(int, data.get('costume'), 0)

        # Weather Info
        self.weather_id = check_for_none(
            int, data.get('weather'), Unknown.TINY)
        self.boosted_weather_id = \
            0 if Unknown.is_not(self.weather_id) else Unknown.TINY
        if is_weather_boosted(self.weather_id, self.mon_id, self.form_id):
            self.boosted_weather_id = self.weather_id
            self.boss_level = 25

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

        # Gym Details (currently only sent from Monocle)
        self.gym_name = check_for_none(
            str, data.get('name'), Unknown.REGULAR).strip()
        self.gym_description = check_for_none(
            str, data.get('description'), Unknown.REGULAR).strip()
        self.gym_image = check_for_none(
            str, data.get('url'), Unknown.REGULAR)
        self.slots_available = Unknown.TINY
        self.guard_count = Unknown.TINY

        self.sponsor_id = check_for_none(
            int, data.get('sponsor'), Unknown.TINY)
        self.park = check_for_none(
            str, data.get('park'), Unknown.REGULAR)
        self.ex_eligible = check_for_none(
            int, data.get('is_ex_raid_eligible'), Unknown.REGULAR)

        # Gym Team (this is only available from cache)
        self.current_team_id = check_for_none(
            int, data.get('team_id', data.get('team')), Unknown.TINY)

        self.name = self.gym_id
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
            if is_weather_boosted(self.weather_id, self.mon_id, self.form_id):
                self.boosted_weather_id = self.weather_id
                self.boss_level = 25

        # Update available slots
        self.slots_available = cache.gym_slots(self.gym_id)
        self.guard_count = (
            (6 - self.slots_available)
            if Unknown.is_not(self.slots_available)
            else Unknown.TINY)

    def generate_dts(self, locale, timezone, units):
        """ Return a dict with all the DTS for this event. """
        raid_end_time = get_time_as_str(self.raid_end, timezone)
        dts = self.custom_dts.copy()

        form_name = locale.get_form_name(self.mon_id, self.form_id)
        evolution_name = locale.get_evolution_name(
            self.evolution_id)
        costume_name = locale.get_costume_name(
            self.mon_id, self.costume_id)

        boosted_weather_name = locale.get_weather_name(self.boosted_weather_id)
        weather_name = locale.get_weather_name(self.weather_id)

        type1 = locale.get_type_name(self.types[0])
        type2 = locale.get_type_name(self.types[1])

        cp_range = get_pokemon_cp_range(
            self.boss_level, self.mon_id, self.form_id)
        dts.update({
            # Identification
            'gym_id': self.gym_id,

            # Time Remaining
            'raid_time_left': raid_end_time[0],
            '12h_raid_end': raid_end_time[1],
            '24h_raid_end': raid_end_time[2],

            # Time Remaining Without Seconds
            'raid_time_no_secs': raid_end_time[3],
            '12h_raid_end_no_secs': raid_end_time[4],
            '24h_raid_end_no_secs': raid_end_time[5],

            # Raw time remaining values
            'raid_time_raw_hours': raid_end_time[6],
            'raid_time_raw_minutes': raid_end_time[7],
            'raid_time_raw_seconds': raid_end_time[8],

            'raid_end_utc': self.raid_end,
            'current_timestamp_utc': datetime.utcnow(),

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
                    self.mon_id, self.form_id) == 'Normal'
                else Unknown.or_empty(form_name)),
            'form_id': self.form_id,
            'form_id_2': "{:02d}".format(self.form_id),
            'form_id_3': "{:03d}".format(self.form_id),

            # Evolution
            'evolution': evolution_name,
            'evolution_or_empty': Unknown.or_empty(evolution_name),
            'evolution_id': self.evolution_id,
            'evolution_id_2': "{:02d}".format(self.evolution_id),
            'evolution_id_3': "{:03d}".format(self.evolution_id),

            # Costume
            'costume': costume_name,
            'costume_or_empty': Unknown.or_empty(costume_name),
            'costume_id': self.costume_id,
            'costume_id_2': "{:02d}".format(self.costume_id),
            'costume_id_3': "{:03d}".format(self.costume_id),

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
            'boosted_weather_emoji': get_weather_emoji(
                self.boosted_weather_id),
            'boosted_or_empty':
                locale.get_boosted_text() if self.boss_level == 25 else '',

            # Raid Info
            'raid_lvl': self.raid_lvl,
            'mon_name': locale.get_pokemon_name(self.mon_id),
            'mon_id': self.mon_id,
            'mon_id_3': "{:03}".format(self.mon_id),
            'gender': self.gender,
            'shiny_emoji': get_shiny_emoji(self.can_be_shiny),

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

            # CP info
            'cp': self.cp,
            'min_cp': cp_range[0],
            'max_cp': cp_range[1],

            # Gym Details
            'gym_name': self.gym_name,
            'gym_description': self.gym_description,
            'gym_image': self.gym_image,
            'slots_available': self.slots_available,
            'guard_count': self.guard_count,
            'sponsor_id': self.sponsor_id,
            'sponsored':
                self.sponsor_id > 0 if Unknown.is_not(self.sponsor_id)
                else Unknown.REGULAR,
            'ex_eligible':
                self.ex_eligible > 0 if Unknown.is_not(self.ex_eligible)
                else Unknown.REGULAR,
            'ex_eligible_emoji': get_ex_eligible_emoji(self.ex_eligible),
            'park': self.park,
            'team_id': self.current_team_id,
            'team_emoji': get_team_emoji(self.current_team_id),
            'team_name': locale.get_team_name(self.current_team_id),
            'team_color': locale.get_team_color(self.current_team_id),
            'team_leader': locale.get_leader_name(self.current_team_id)
        })
        return dts
