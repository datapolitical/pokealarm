# Standard Library Imports
import operator
# 3rd Party Imports
# Local Imports
from . import BaseFilter
from PokeAlarm.Utilities import MonUtils as MonUtils
from PokeAlarm.Utilities import GymUtils as GymUtils
from PokeAlarm.Utils import get_weather_id, match_items_in_array, \
    get_gender_sym


class RaidFilter(BaseFilter):
    """ Filter class for limiting which egg trigger a notification. """

    def __init__(self, mgr, name, data, geofences_ref=None):
        """ Initializes base parameters for a filter. """
        super(RaidFilter, self).__init__(mgr, 'egg', name, geofences_ref)

        # Monster ID - f.mon_ids in r.mon_id
        self.mon_ids = self.evaluate_attribute(  #
            event_attribute='mon_id', eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(
                MonUtils.get_monster_id, 'monsters', data))

        # Exclude Monster ID - f.monster_ids not contains r.ex_mon_id
        self.exclude_mon_ids = self.evaluate_attribute(  #
            event_attribute='mon_id',
            eval_func=lambda d, v: not operator.contains(d, v),
            limit=BaseFilter.parse_as_set(
                MonUtils.get_monster_id, 'monsters_exclude', data))

        # Pokemon types
        self.type_ids = self.evaluate_attribute(  # one mon_type in types
            event_attribute='types', eval_func=match_items_in_array,
            limit=BaseFilter.parse_as_list(
                MonUtils.get_type_id, 'types', data))

        # Distance
        self.min_dist = self.evaluate_attribute(  # f.min_dist <= r.distance
            event_attribute='distance', eval_func=operator.le,
            limit=BaseFilter.parse_as_type(float, 'min_dist', data))
        self.max_dist = self.evaluate_attribute(  # f.max_dist <= r.distance
            event_attribute='distance', eval_func=operator.ge,
            limit=BaseFilter.parse_as_type(float, 'max_dist', data))

        # Time Left
        self.min_time_left = self.evaluate_attribute(
            # f.min_time_left <= r.time_left
            event_attribute='time_left', eval_func=operator.le,
            limit=BaseFilter.parse_as_type(int, 'min_time_left', data))
        self.max_time_left = self.evaluate_attribute(
            # f.max_time_left >= r.time_left
            event_attribute='time_left', eval_func=operator.ge,
            limit=BaseFilter.parse_as_type(int, 'max_time_left', data))

        # Monster Info
        self.min_lvl = self.evaluate_attribute(  # f.min_lvl <= r.mon_lvl
            event_attribute='raid_lvl', eval_func=operator.le,
            limit=BaseFilter.parse_as_type(int, 'min_raid_lvl', data))
        self.max_lvl = self.evaluate_attribute(  # f.max_lvl >= r.mon_lvl
            event_attribute='raid_lvl', eval_func=operator.ge,
            limit=BaseFilter.parse_as_type(int, 'max_raid_lvl', data))

        # Monster Forms
        self.forms = self.evaluate_attribute(  # f.forms in r.form_id
            event_attribute='form_id', eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(int, 'form_ids', data))
        # Exclude Forms - f.forms_ids not contains m.ex_form_id
        self.exclude_form_ids = self.evaluate_attribute(  #
            event_attribute='form_id',
            eval_func=lambda d, v: not operator.contains(d, v),
            limit=BaseFilter.parse_as_set(int, 'exclude_forms', data))

        # Monster Costumes
        self.costumes = self.evaluate_attribute(  # f.costumes in m.costume_id
            event_attribute='costume_id', eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(int, 'costume_ids', data))
        # Exclude Costumes - f.costumes_ids not contains m.ex_costume_id
        self.exclude_costume_ids = self.evaluate_attribute(  #
            event_attribute='costume_id',
            eval_func=lambda d, v: not operator.contains(d, v),
            limit=BaseFilter.parse_as_set(int, 'exclude_costumes', data))

        # Cosmetic
        self.can_be_shiny = self.evaluate_attribute(
            event_attribute='can_be_shiny',
            eval_func=operator.eq,
            limit=BaseFilter.parse_as_type(bool, 'can_be_shiny', data))

        # Gender
        self.genders = self.evaluate_attribute(  # f.genders contains m.gender
            event_attribute='gender', eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(
                get_gender_sym, 'genders', data))

        # CP
        self.min_cp = self.evaluate_attribute(  # f.min_cp <= r.cp
            event_attribute='cp', eval_func=operator.le,
            limit=BaseFilter.parse_as_type(int, 'min_cp', data))
        self.max_cp = self.evaluate_attribute(  # f.max_cp >= r.cp
            event_attribute='cp', eval_func=operator.ge,
            limit=BaseFilter.parse_as_type(int, 'max_cp', data))

        # Quick Move
        self.quick_moves = self.evaluate_attribute(  # f.q_ms contains r.q_m
            event_attribute='quick_id', eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(
                MonUtils.get_move_id, 'quick_moves', data))

        # Charge Move
        self.charge_moves = self.evaluate_attribute(  # f.c_ms contains r.c_m
            event_attribute='charge_id', eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(
                MonUtils.get_move_id, 'charge_moves', data))

        # Gym name
        self.gym_name_contains = self.evaluate_attribute(  # f.gn matches e.gn
            event_attribute='gym_name', eval_func=GymUtils.match_regex_dict,
            limit=BaseFilter.parse_as_set(
                GymUtils.create_regex, 'gym_name_contains', data))
        self.gym_name_excludes = self.evaluate_attribute(  # f.gn no-match e.gn
            event_attribute='gym_name',
            eval_func=GymUtils.not_match_regex_dict,
            limit=BaseFilter.parse_as_set(
                GymUtils.create_regex, 'gym_name_excludes', data))

        # Gym sponsor
        self.sponsored = self.evaluate_attribute(  #
            event_attribute='sponsor_id', eval_func=lambda y, x: (x > 0) == y,
            limit=BaseFilter.parse_as_type(bool, 'sponsored', data))

        # Gym park
        self.park_contains = self.evaluate_attribute(  # f.gp matches e.gp
            event_attribute='park', eval_func=GymUtils.match_regex_dict,
            limit=BaseFilter.parse_as_set(
                GymUtils.create_regex, 'park_contains', data))

        self.is_ex_eligible = self.evaluate_attribute(
            event_attribute='ex_eligible',
            eval_func=operator.eq,
            limit=BaseFilter.parse_as_type(bool, 'is_ex_eligible', data)
        )

        # Team Info
        self.old_team = self.evaluate_attribute(  # f.ctis contains m.cti
            event_attribute='current_team_id', eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(
                GymUtils.get_team_id, 'current_teams', data))

        # Weather
        self.weather_ids = self.evaluate_attribute(  # f.w_ids contains m.w_id
            event_attribute='weather_id', eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(get_weather_id, 'weather', data))

        # Geofences
        self.geofences = self.evaluate_geofences(
            geofences=BaseFilter.parse_as_list(str, 'geofences', data),
            exclude_mode=False)
        self.exclude_geofences = self.evaluate_geofences(
            geofences=BaseFilter.parse_as_list(str, 'exclude_geofences', data),
            exclude_mode=True)

        # Time
        self.evaluate_time(BaseFilter.parse_as_time(
            'min_time', data), BaseFilter.parse_as_time('max_time', data))

        # Custom DTS
        self.custom_dts = BaseFilter.parse_as_dict(
            str, str, 'custom_dts', data)

        # Missing Info
        self.is_missing_info = BaseFilter.parse_as_type(
            bool, 'is_missing_info', data)

        # Reject leftover parameters
        for key in data:
            raise ValueError("'{}' is not a recognized parameter for"
                             " Raid filters".format(key))

    def to_dict(self):
        """ Create a dict representation of this Filter. """
        settings = {}
        # Monster ID
        if self.mon_ids is not None:
            settings['monster_ids'] = self.mon_ids

        # Pokemon types
        if self.type_ids is not None:
            settings['type_ids'] = self.type_ids

        # Distance
        if self.min_dist is not None:
            settings['min_dist'] = self.min_dist
        if self.max_dist is not None:
            settings['max_dist'] = self.max_dist

        # Level
        if self.min_lvl is not None:
            settings['min_lvl'] = self.min_lvl
        if self.max_lvl is not None:
            settings['max_lvl'] = self.max_lvl

        # Form
        if self.forms is not None:
            settings['forms'] = self.forms

        # Gender
        if self.genders is not None:
            settings['genders'] = self.genders

        # Cosmetic
        if self.can_be_shiny is not None:
            settings['can_be_shiny'] = self.can_be_shiny

        # Weather
        if self.weather_ids is not None:
            settings['weather_ids'] = self.weather_ids

        # Gym Name
        if self.gym_name_contains is not None:
            settings['gym_name_contains'] = self.gym_name_contains

        if self.gym_name_excludes is not None:
            settings['gym_name_excludes'] = self.gym_name_excludes

        # Gym Sponsor
        if self.sponsored is not None:
            settings['sponsored'] = self.sponsored

        # Gym Park
        if self.park_contains is not None:
            settings['park_contains'] = self.park_contains

        # Geofences
        if self.geofences is not None:
            settings['geofences'] = self.geofences
        if self.exclude_geofences is not None:
            settings['exclude_geofences'] = self.exclude_geofences

        # Missing Info
        if self.is_missing_info is not None:
            settings['is_missing_info'] = self.is_missing_info

        return settings
