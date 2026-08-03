from BaseClasses import Location

# Base location ID. 
# Annie's copies of doubled checks live at +5000.
LOC_OFFSET = 42000000
ANNIE_OFFSET = 5000

class AntonLocationData:
    def __init__(self, code: int, region: str, stage_key: str = ''):
        self.code = code
        self.region = region
        self.stage_key = stage_key

class AntonLocation(Location):
    game = 'Antonblast'

# name = AntonLocationData for every check in the game
location_table: dict[str, AntonLocationData] = {}

def _add(name: str, code: int, region: str, stage_key: str = '') -> None:
    location_table[name] = AntonLocationData(code, region, stage_key)

# Registers the Annie copy of a check (dual character mode only).
def _add_annie(name: str, anton_code: int, region: str, stage_key: str = '') -> None:
    annie_name = f'Annie - {name}'
    annie_region = f'Annie - {region}'
    annie_code = LOC_OFFSET + ANNIE_OFFSET + (anton_code - LOC_OFFSET)
    location_table[annie_name] = AntonLocationData(annie_code, annie_region, stage_key)

# (display name, internal stage key used by the game)
STAGES = [
    ('Boiler City', 'boilerCity'),
    ('Slowroast Sewer', 'slowroastSewer'),
    ('Cinnamon Springs', 'cinnamonSprings'),
    ('Bomb Candy Mines', 'bombCandyMines'),
    ('The Big Bath', 'theBigBath'),
    ('Concrete Jungle', 'concreteJungle'),
    ('The Mad Mall', 'theMadMall'),
    ('Pinball Mire', 'pinballMire'),
    ('Crimson Factory', 'crimsonFactory'),
    ('The Mysterious Glasshouse', 'theMysteriousGlasshouse'),
    ('Devilled Gardens', 'devilledGardens'),
    ('Hell Manor', 'hellManor')
]

BOSSES = [
    ('Brawlbuster', 'brawlbuster'),
    ('Jewel Ghoul', 'jewelGhoul'),
    ('Tallbuster', 'tallbuster'),
    ('Freako Dragon', 'freakoDragon'),
    ('Smallbuster', 'smallbuster'),
    ('Maulbuster', 'maulbuster'),
    ('Ring-A-Ding', 'ringADing'),
    ('Satan', 'satan')
]

EX_BOSSES = [
    ('Kaz', 'kaz'),
    ('Parrot', 'parrot'),
    ('Computer', 'computer'),
    ('Chameleon', 'chameleon'),
    ('Tag Team', 'tagTeam')
]

LIMES = [
    ('Shark Tank', 'sharkTank'),
    ('Limes a Beach', 'limesABeach'),
    ('Distilled Hill', 'distilledHill'),
    ('Devil\'s a Beach', 'devilsABeach')
]

SHOP_TRINKETS = [
    'Trinket: Shutter Shades',
    'Trinket: Cowboy Hat',
    'Trinket: Funny TV',
    'Trinket: Funny TV Big',
    'Trinket: Pet Color',
    'Screen Palette: VB',
    'Screen Palette: GB'
]

SHOP_VINYLS = [
    'Shop Vinyl: Collen Cyte',
    'Shop Vinyl: Element 27',
    'Shop Vinyl: Fred Fuchs',
    'Shop Vinyl: Joseph Cassin',
    'Shop Vinyl: Logan Gerrol',
    'Shop Vinyl: Pear Basket',
    'Shop Vinyl: Rom M',
    'Shop Vinyl: Impetus',
    'Shop Vinyl: William'
]

UPGRADES = [
    'HP Beet Up',
    'Bonus HP Up',
    'Balloon Add-On',
    'Pet Add-On',
    'Spirit Timer Add-On'
]

DETONATOR_SUITS = ['Club', 'Diamond', 'Heart', 'Spade']

# Stage collectibles
_off = 0
for _stage_name, _stage_key in STAGES:
    _code = LOC_OFFSET + _off
    _add(f'Vinyl: {_stage_name}', _code + 0, _stage_name, _stage_key)
    _add(f'Trash: {_stage_name}', _code + 1, _stage_name, _stage_key)
    _add(f'Spray: {_stage_name}', _code + 2, _stage_name, _stage_key)
    _add(f'Spirit: {_stage_name}', _code + 3, _stage_name, _stage_key)
    _add_annie(f'Vinyl: {_stage_name}', _code + 0, _stage_name, _stage_key)
    _add_annie(f'Trash: {_stage_name}', _code + 1, _stage_name, _stage_key)
    _add_annie(f'Spray: {_stage_name}', _code + 2, _stage_name, _stage_key)
    _add_annie(f'Spirit: {_stage_name}', _code + 3, _stage_name, _stage_key)
    _off += 10

# Stage clears
_clear_off = 150
for _stage_name, _stage_key in STAGES:
    _add(f'Clear: {_stage_name}', LOC_OFFSET + _clear_off, _stage_name, _stage_key)
    _add_annie(f'Clear: {_stage_name}', LOC_OFFSET + _clear_off, _stage_name, _stage_key)
    _clear_off += 1

# Boss clears
_boss_off = 200
for _boss_name, _boss_key in BOSSES:
    _add(f'Clear: {_boss_name}', LOC_OFFSET + _boss_off, _boss_name, _boss_key)
    _boss_off += 1

# EX boss clears
_ex_off = 250
for _boss_name, _boss_key in EX_BOSSES:
    _add(f'Clear: {_boss_name}', LOC_OFFSET + _ex_off, _boss_name, _boss_key)
    _ex_off += 1

# Lime trial clears
_lime_off = 300
for _lime_name, _lime_key in LIMES:
    _add(f'Clear: {_lime_name}', LOC_OFFSET + _lime_off, _lime_name, _lime_key)
    _lime_off += 1

# Shop purchases
_shop_off = 320
for _trinket_name in SHOP_TRINKETS:
    _add(_trinket_name, LOC_OFFSET + _shop_off, 'Shop', '')
    _shop_off += 1

_shop_vinyl_off = 335
for _vinyl_name in SHOP_VINYLS:
    _add(_vinyl_name, LOC_OFFSET + _shop_vinyl_off, 'Shop', '')
    _shop_vinyl_off += 1

_upgrade_off = 360
for _upgrade_name in UPGRADES:
    _add(f'Buy: {_upgrade_name}', LOC_OFFSET + _upgrade_off, 'Shop', '')
    _upgrade_off += 1

# Stage checkpoints (The Mad Mall has no physical checkpoint, skipped)
_checkpoint_off = 400
for _stage_name, _stage_key in STAGES:
    if _stage_key != 'theMadMall':
        _add(f'Checkpoint: {_stage_name}', LOC_OFFSET + _checkpoint_off, _stage_name, _stage_key)
        _add_annie(f'Checkpoint: {_stage_name}', LOC_OFFSET + _checkpoint_off, _stage_name, _stage_key)
    _checkpoint_off += 1

# Goal
_add('Goal: Defeat Satan', LOC_OFFSET + 500, 'Satan', 'satan')

# Detonators
DETONATOR_LOCS: dict[str, list[int]] = {}
for _i, (_stage_name, _stage_key) in enumerate(STAGES):
    DETONATOR_LOCS[_stage_key] = []
    for _s, _suit in enumerate(DETONATOR_SUITS):
        # A small fix for the DUMB detonator of MGH grr
        if _stage_key == 'theMysteriousGlasshouse' and _suit == 'Diamond':
            continue
        _code = LOC_OFFSET + 600 + (_i * 10) + _s
        _add(f'{_suit} Detonator: {_stage_name}', _code, _stage_name, _stage_key)
        _add_annie(f'{_suit} Detonator: {_stage_name}', _code, _stage_name, _stage_key)
        DETONATOR_LOCS[_stage_key].append(_code)

# Time trials (par time beaten)
TIME_TRIAL_LOCS: dict[str, int] = {}
_par_off = 42200000
for _stage_name, _stage_key in STAGES:
    _add(f'Time Trial: {_stage_name}', _par_off, _stage_name, _stage_key)
    _add_annie(f'Time Trial: {_stage_name}', _par_off, _stage_name, _stage_key)
    TIME_TRIAL_LOCS[_stage_key] = _par_off
    _par_off += 1

# Cracked rank
CRACKED_LOCS: dict[str, int] = {}
_cracked_off = 42200100
for _stage_name, _stage_key in STAGES:
    _add(f'Cracked: {_stage_name}', _cracked_off, _stage_name, _stage_key)
    _add_annie(f'Cracked: {_stage_name}', _cracked_off, _stage_name, _stage_key)
    CRACKED_LOCS[_stage_key] = _cracked_off
    _cracked_off += 1

for _boss_name, _boss_key in BOSSES:
    if _boss_name == 'Satan':
        continue
        
    _add(f'Cracked: {_boss_name}', _cracked_off, _boss_name, _boss_key)
    _add_annie(f'Cracked: {_boss_name}', _cracked_off, _boss_name, _boss_key)
    CRACKED_LOCS[_boss_key] = _cracked_off
    _cracked_off += 1

# Pauls
PAUL_LOCS: dict[str, int] = {}
_paul_off = 42200200
for _stage_name, _stage_key in STAGES:
    _add(f'Paul: {_stage_name}', _paul_off, _stage_name, _stage_key)
    _add_annie(f'Paul: {_stage_name}', _paul_off, _stage_name, _stage_key)
    PAUL_LOCS[_stage_key] = _paul_off
    _paul_off += 1

# Red rooms (secret VB rooms, only these 6 exist), named after the ingame room
RED_ROOMS = [
    ('Classic Bounce Training', 'Boiler City', 'boilerCity'),
    ('Crimson Cave Dive', 'Cinnamon Springs', 'cinnamonSprings'),
    ('Crimson Concrete', 'Concrete Jungle', 'concreteJungle'),
    ('Red Your Rights', 'The Mad Mall', 'theMadMall'),
    ('Bonus Round', 'Crimson Factory', 'crimsonFactory'),
    ('Irritating Mosquito Room', 'The Mysterious Glasshouse', 'theMysteriousGlasshouse')
]

RED_ROOM_LOCS: dict[str, int] = {}
_red_off = 42200250
for _room_name, _stage_name, _stage_key in RED_ROOMS:
    _add(f'Red Room: {_room_name}', _red_off, _stage_name, _stage_key)
    _add_annie(f'Red Room: {_room_name}', _red_off, _stage_name, _stage_key)
    RED_ROOM_LOCS[_stage_key] = _red_off
    _red_off += 1

ALL_STAGE_REGIONS = [s[0] for s in STAGES]
ALL_BOSS_REGIONS = [b[0] for b in BOSSES]
ALL_EX_REGIONS = [b[0] for b in EX_BOSSES]
ALL_LIME_REGIONS = [l[0] for l in LIMES]

# yaml option key = stage display name
OPTION_KEY_TO_STAGE = {
    'boiler_city': 'Boiler City',
    'slowroast_sewer': 'Slowroast Sewer',
    'cinnamon_springs': 'Cinnamon Springs',
    'bomb_candy_mines': 'Bomb Candy Mines',
    'the_big_bath': 'The Big Bath',
    'concrete_jungle': 'Concrete Jungle',
    'the_mad_mall': 'The Mad Mall',
    'pinball_mire': 'Pinball Mire',
    'crimson_factory': 'Crimson Factory',
    'the_mysterious_glasshouse': 'The Mysterious Glasshouse',
    'devilled_gardens': 'Devilled Gardens',
    'hell_manor': 'Hell Manor'
}

STAGE_TO_KEY_ITEM = {s: f'Level Key: {s}' for s, _ in STAGES + BOSSES + EX_BOSSES + LIMES}
