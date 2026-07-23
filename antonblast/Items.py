from BaseClasses import Item, ItemClassification

# Base item ID, kept away from the location range.
ITEM_OFFSET = 42100000

class AntonItemData:
    def __init__(self, code: int, classification: ItemClassification, quantity: int = 1):
        self.code = code
        self.classification = classification
        self.quantity = quantity

class AntonItem(Item):
    game = 'Antonblast'

def _key(code: int) -> AntonItemData:
    return AntonItemData(ITEM_OFFSET + code, ItemClassification.progression)

def _useful(code: int) -> AntonItemData:
    return AntonItemData(ITEM_OFFSET + code, ItemClassification.useful)

def _prog(code: int) -> AntonItemData:
    return AntonItemData(ITEM_OFFSET + code, ItemClassification.progression)

def _filler(code: int) -> AntonItemData:
    return AntonItemData(ITEM_OFFSET + code, ItemClassification.filler)

# name = AntonItemData for everything the game can receive
item_table: dict[str, AntonItemData] = {}

# Level keys
_KEY_NAMES = [
    'Boiler City', 'Slowroast Sewer', 'Brawlbuster', 'Cinnamon Springs',
    'Bomb Candy Mines', 'Jewel Ghoul', 'The Big Bath', 'Tallbuster',
    'Concrete Jungle', 'Pinball Mire', 'Freako Dragon', 'The Mad Mall',
    'Smallbuster', 'Crimson Factory', 'Maulbuster', 'The Mysterious Glasshouse',
    'Ring-A-Ding', 'Devilled Gardens', 'Hell Manor', 'Satan',
    'Shark Tank', 'Limes a Beach', 'Distilled Hill', 'Devil\'s a Beach',
    'Kaz', 'Parrot', 'Computer', 'Chameleon', 'Tag Team'
]

for _i, _name in enumerate(_KEY_NAMES):
    item_table[f'Level Key: {_name}'] = _key(_i)

# Stage collectibles
_COLLECTIBLE_SETS = [
    ('Vinyl: Boiler City', 'Trash: TV', 'Spray: City', 'Spirit: Boiler City'),
    ('Vinyl: Slowroast Sewer', 'Trash: Banana', 'Spray: Sewer', 'Spirit: Slowroast Sewer'),
    ('Vinyl: Cinnamon Springs', 'Trash: Hot Chip', 'Spray: Springs', 'Spirit: Cinnamon Springs'),
    ('Vinyl: Bomb Candy Mines', 'Trash: Mini Mitt', 'Spray: Mines', 'Spirit: Bomb Candy Mines'),
    ('Vinyl: The Big Bath', 'Trash: Virtual Pippo', 'Spray: Bath', 'Spirit: The Big Bath'),
    ('Vinyl: Concrete Jungle', 'Trash: Controller', 'Spray: Jungle', 'Spirit: Concrete Jungle'),
    ('Vinyl: The Mad Mall', 'Trash: Ballble Tea', 'Spray: Mall', 'Spirit: The Mad Mall'),
    ('Vinyl: Pinball Mire', 'Trash: Bottle Cap', 'Spray: Mire', 'Spirit: Pinball Mire'),
    ('Vinyl: Crimson Factory', 'Trash: Car', 'Spray: Factory', 'Spirit: Crimson Factory'),
    ('Vinyl: The Mysterious Glasshouse', 'Trash: Trophy', 'Spray: Glasshouse', 'Spirit: The Mysterious Glasshouse'),
    ('Vinyl: Devilled Gardens', 'Trash: Headphones', 'Spray: Gardens', 'Spirit: Devilled Gardens'),
    ('Vinyl: Hell Manor', 'Trash: Tallbuster', 'Spray: Manor', 'Spirit: Hell Manor')
]

_code = 100
for _vinyl, _trash, _spray, _spirit in _COLLECTIBLE_SETS:
    item_table[_vinyl] = _useful(_code + 0)
    item_table[_trash] = _useful(_code + 1)
    item_table[_spray] = _useful(_code + 2)
    item_table[_spirit] = _prog(_code + 3)
    _code += 4

# Boss spirits
_BOSS_SPIRITS = ['Brawlbuster', 'Jewel Ghoul', 'Tallbuster', 'Freako Dragon', 'Smallbuster', 'Maulbuster', 'Ring-A-Ding']

for _i, _name in enumerate(_BOSS_SPIRITS):
    item_table[f'Boss Spirit: {_name}'] = _prog(200 + _i)

# Lets the player switch to playable Paul without the 12-Paul requirement
item_table['Paul Unlock'] = _useful(217)

# Upgrades
item_table['HP Beet Up'] = _useful(300)
item_table['Bonus HP Up'] = _useful(301)
item_table['Balloon Add-On'] = _useful(302)
item_table['Pet Add-On'] = _useful(303)
item_table['Spirit Timer Add-On'] = _useful(304)

# Shop trinkets and palettes
item_table['Trinket: Shutter Shades'] = _useful(305)
item_table['Trinket: Cowboy Hat'] = _useful(306)
item_table['Trinket: Funny TV'] = _useful(307)
item_table['Trinket: Funny TV Big'] = _useful(308)
item_table['Trinket: Pet Color'] = _useful(309)
item_table['Screen Palette: VB'] = _useful(310)
item_table['Screen Palette: GB'] = _useful(311)

# Shop vinyls
_SHOP_VINYLS = ['Collen Cyte', 'Element 27', 'Fred Fuchs', 'Joseph Cassin', 'Logan Gerrol', 'Pear Basket', 'Rom M', 'Impetus', 'William']

for _i, _name in enumerate(_SHOP_VINYLS):
    item_table[f'Shop Vinyl: {_name}'] = _useful(312 + _i)

# Coin filler
item_table['Small Coins'] = _filler(400)
item_table['Large Coins'] = _filler(401)
item_table['Jackpot Coins'] = _filler(402)

item_groups = {
    'keys': [n for n in item_table if n.startswith('Level Key:')],
    'collectibles': [n for n in item_table if any(n.startswith(x) for x in ['Vinyl:', 'Trash:', 'Spray:', 'Spirit:'])],
    'upgrades': [n for n in item_table if any(n.startswith(x) for x in ['HP', 'Bonus', 'Balloon', 'Pet', 'Spirit Timer'])],
    'trinkets': [n for n in item_table if n.startswith('Trinket:') or n.startswith('Screen Palette:')],
    'shop_vinyls': [n for n in item_table if n.startswith('Shop Vinyl:')],
    'coins': ['Small Coins', 'Large Coins', 'Jackpot Coins'],
    'skins': []
}
