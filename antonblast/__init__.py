from BaseClasses import Item
from worlds.AutoWorld import World
from worlds.LauncherComponents import Component, components, Type, launch_subprocess, icon_paths

from .Items import AntonItem, item_table, item_groups
from .Locations import (AntonLocation, location_table, ALL_STAGE_REGIONS, OPTION_KEY_TO_STAGE, STAGE_TO_KEY_ITEM, EX_BOSSES, LIMES)
from .Regions import create_regions
from .Rules import set_rules
from .Options import AntonOptions

def launch_client(*args: str) -> None:
    from .Client import launch
    launch_subprocess(launch, name='Antonblast Client', args=args)

icon_paths['antonblast'] = f'ap:{__name__}/data/icon.png'
components.append(Component('Antonblast Client', 'AntonblastClient', func=launch_client, component_type=Type.CLIENT, icon='antonblast'))

class AntonWorld(World):
    required_client_version = (0, 0, 0)
    game = 'Antonblast'
    topology_present = False

    item_name_to_id = {name: data.code for name, data in item_table.items()}
    location_name_to_id = {name: data.code for name, data in location_table.items()}

    item_name_groups = item_groups
    options_dataclass = AntonOptions
    options: AntonOptions

    def create_item(self, name: str) -> Item:
        data = item_table[name]
        return AntonItem(name, data.classification, data.code, self.player)

    def _get_starting_stage_display(self) -> str:
        return OPTION_KEY_TO_STAGE.get(self.options.starting_stage.current_key, 'Boiler City')

    # The starting stage's key is precollected so the seed is always startable. (Yeah very dumb fix to be honest.)
    def generate_early(self) -> None:
        if self.options.stage_unlock_mode:
            starting = self._get_starting_stage_display()
            key_name = f'Level Key: {starting}'

            if key_name in item_table:
                self.multiworld.push_precollected(self.create_item(key_name))

    # Builds the item pool, skipping anything the options disabled,
    # then tops it up with coin filler to match the location count.
    def create_items(self) -> None:
        exclude: set[str] = set()

        if self.options.stage_unlock_mode:
            starting = self._get_starting_stage_display()
            exclude.add(f'Level Key: {starting}')

        if not self.options.include_ex_bosses:
            for boss_name, _ in EX_BOSSES:
                exclude.add(f'Level Key: {boss_name}')

        if not self.options.include_lime_trials:
            for lime_name, _ in LIMES:
                exclude.add(f'Level Key: {lime_name}')

        pool: list[Item] = []
        for name, data in item_table.items():
            if name in exclude:
                continue

            if not self.options.include_shop_items and (name.startswith('Trinket:') or name.startswith('Screen Palette:') or name.startswith('Shop Vinyl:')):
                continue

            for _ in range(data.quantity):
                pool.append(self.create_item(name))

        location_count = len(self.multiworld.get_unfilled_locations(self.player))
        while len(pool) < location_count:
            pool.append(self.create_item(self.get_filler_item_name()))

        self.multiworld.itempool += pool

    def get_filler_item_name(self) -> str:
        import random
        return random.choice(['Small Coins', 'Large Coins', 'Jackpot Coins'])

    def create_regions(self) -> None:
        create_regions(self.multiworld, self.player, self.options)

    def set_rules(self) -> None:
        set_rules(self.multiworld, self.player, self.options)

    def generate_output(self, output_directory: str) -> None:
        pass

    # Everything the client forwards to the game as CONFIG messages1!!1!
    def fill_slot_data(self) -> dict:
        return {
            'stage_unlock_mode': bool(self.options.stage_unlock_mode),
            'dual_character': bool(self.options.dual_character),
            'character': int(self.options.character.value),
            'starting_stage': self.options.starting_stage.current_key,
            'goal': self.options.goal.current_key,
            'include_time_trials': bool(self.options.include_time_trials),
            'time_trial_mult': int(self.options.time_trial_mult.value),
            'include_cracked': bool(self.options.include_cracked),
            'include_detonators': bool(self.options.include_detonators),
            'include_pauls': bool(self.options.include_pauls),
            'include_red_rooms': bool(self.options.include_red_rooms),
            'coin_multiplier': int(self.options.coin_multiplier.value),
            'death_link': bool(self.options.death_link)
        }
