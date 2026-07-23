import asyncio
import re
import time

from collections import deque
from CommonClient import CommonContext, gui_enabled, ClientCommandProcessor, logger, get_base_parser

DEFAULT_HTTP_PORT = 42069
DEFAULT_AP_PORT = 38281
GAME_TIMEOUT_SECONDS = 30.0

TRASH_OBJECTS = [
    'ob_trashTv', 'ob_trashBanana', 'ob_trashHotChip', 'ob_trashMiniMitt',
    'ob_trashVirtualPippo', 'ob_trashController', 'ob_trashBallbleTea',
    'ob_trashBottleCap', 'ob_trashCar', 'ob_trashTrophy',
    'ob_trashHeadphones', 'ob_trashTallbuster'
]

SPIRIT_OBJECTS = [
    'ob_spiritWonga', 'ob_spiritSewer', 'ob_spiritBallba', 'ob_spiritMines',
    'ob_spiritShampoo', 'ob_spiritCoffee', 'ob_spiritCola', 'ob_spiritSweaty',
    'ob_spiritSoda', 'ob_spiritGlasshouse', 'ob_spiritPolar', 'ob_spiritDevilsBrew'
]

class AntonblastContext(CommonContext):
    game = 'Antonblast'
    tags = {'AP'}

    def __init__(self, server_address, password):
        super().__init__(server_address, password)
        self.items_handling = 0b111

        # game link state
        self.game_connected = False
        self.config_sent = False
        self.last_poll_time: float = 0.0
        self._disconnect_notified = False

        # outgoing messages for the game, drained on every poll
        self.game_item_queue: deque[str] = deque()

        # caches replayed to the game on every new handshake
        self.scout_cache: list[str] = []
        self.checked_cache: list[str] = []

        # highest ReceivedItems index forwarded so far
        self.items_last_index = 0

        self.slot_data: dict = {}
        self.last_death_link = 0.0

    # AP server side
    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)

        await self.get_username()
        await self.send_connect()

    def on_deathlink(self, data: dict) -> None:
        super().on_deathlink(data)
        cause = str(data.get('cause', 'Unknown')).replace('|', '-').replace('\n', ' ')
        self.game_item_queue.append('DEATH|' + cause)

    def on_package(self, cmd: str, args: dict) -> None:
        try:
            super().on_package(cmd, args)
        except Exception as e:
            logger.error(f'Error in super().on_package: {e}')

        try:
            self._handle_package(cmd, args)
        except Exception as e:
            logger.error(f'Error handling {cmd} packet: {e}')

    def _handle_package(self, cmd: str, args: dict) -> None:
        if cmd == 'Connected':
            self._on_connected(args)
        elif cmd == 'RoomUpdate':
            self._on_room_update(args)
        elif cmd == 'ReceivedItems':
            self._on_received_items(args)
        elif cmd == 'LocationInfo':
            self._on_location_info(args)

    def _on_connected(self, args: dict) -> None:
        self.slot_data = args.get('slot_data', {}) or {}
        logger.info('Connected to Archipelago server!')

        self.scout_cache.clear()
        self.config_sent = False
        self.items_last_index = 0
        self._update_config_file()

        if self.slot_data.get('death_link', False):
            asyncio.ensure_future(self.update_death_link(True))

        self.game_item_queue.append(self._session_message())

        # tell the game which checks the server already counted
        self.checked_cache = ['CHECKED|' + str(l) for l in sorted(self.checked_locations)]
        for msg in self.checked_cache:
            self.game_item_queue.append(msg)

        # scout everything so the game knows what each check contains
        all_locs = list(self.missing_locations | self.checked_locations)
        if all_locs:
            asyncio.ensure_future(self.send_msgs([{
                'cmd': 'LocationScouts',
                'locations': all_locs,
                'create_as_hint': 0
            }]))

    def _on_room_update(self, args: dict) -> None:
        # forward newly checked locations
        for l in args.get('checked_locations', []) or []:
            msg = 'CHECKED|' + str(l)

            if msg not in self.checked_cache:
                self.checked_cache.append(msg)
                self.game_item_queue.append(msg)

    def _on_received_items(self, args: dict) -> None:
        start_index = args.get('index', 0)
        for i, item in enumerate(args['items']):
            global_index = start_index + i
            
            if global_index < self.items_last_index:
                continue
            
            self.items_last_index = global_index + 1
            self.game_item_queue.append(self._item_message(item, global_index))

    def _on_location_info(self, args: dict) -> None:
        for item in args.get('locations', []):
            scout_msg = self._scout_message(item)
            self.game_item_queue.append(scout_msg)
            self.scout_cache.append(scout_msg)

    # message builders
    @staticmethod
    def _net_item_fields(item) -> tuple:
        item_id = item.item if hasattr(item, 'item') else item[0]
        loc_id = item.location if hasattr(item, 'location') else item[1]
        item_player = item.player if hasattr(item, 'player') else item[2]

        return item_id, loc_id, item_player

    def _player_name(self, player: int) -> str:
        name = self.player_names.get(player, f'Player{player}')
        return str(name).replace('|', '-').replace('\n', ' ')

    def _item_message(self, item, index: int) -> str:
        item_id, _, item_player = self._net_item_fields(item)
        return 'ITEM|' + str(int(item_id)) + '|' + self._player_name(item_player) + '|' + str(index)

    def _session_message(self) -> str:
        slot_name = self.player_names.get(self.slot, '') if self.slot else ''
        seed_name = getattr(self, 'seed_name', '') or ''

        return 'SESSION|' + str(slot_name) + '|' + str(seed_name) + '|' + str(self._get_real_port())

    def _scout_message(self, item) -> str:
        item_id, loc_id, item_player = self._net_item_fields(item)
        is_foreign = 1 if item_player != self.slot else 0
        cat, ob_name = self._get_item_info(item_id, item_player)

        item_name = ''
        try:
            if hasattr(self, 'item_names') and hasattr(self, 'slot_info') and item_player in self.slot_info:
                game = self.slot_info[item_player].game
                item_name = str(self.item_names[game][item_id])
            elif hasattr(self, 'item_names'):
                item_name = str(self.item_names[self.game][item_id])
        except Exception:
            item_name = getattr(item, 'name', '') or ''

        item_name = (item_name or '').replace('|', '-').replace('\n', ' ')
        player_name = self._player_name(item_player) if item_player != self.slot else ''

        return f'SCOUT|{loc_id}|{is_foreign}|{cat}|{ob_name}|{item_name}|{player_name}'

    # Classifies an item for ingame rendering
    def _get_item_info(self, item_id: int, item_player: int) -> tuple:
        if item_player != self.slot:
            return 'ap', ''

        from worlds.antonblast.Items import ITEM_OFFSET
        rel = item_id - ITEM_OFFSET

        if 0 <= rel < 100:
            return 'key', ''

        if 100 <= rel < 200:
            stage_idx = (rel - 100) // 4
            type_idx = (rel - 100) % 4
            cats = ['vinyl', 'trash', 'spray', 'spirit']
            ob_lists = [['ob_vinyl'] * 12, TRASH_OBJECTS, ['ob_spraycan'] * 12, SPIRIT_OBJECTS]
            cat = cats[type_idx]
            ob_list = ob_lists[type_idx]
            ob_name = ob_list[stage_idx] if stage_idx < len(ob_list) else ''

            return cat, ob_name

        if 200 <= rel <= 207:
            return 'spirit', 'ob_spiritWonga'

        return 'ap', ''

    # All CONFIG lines derived from slot data and the session line.
    def _build_config_messages(self) -> list[str]:
        slot_data = self.slot_data or {}
        msgs = []

        def flag(key: str, default: bool) -> str:
            return '1' if slot_data.get(key, default) else '0'

        msgs.append('CONFIG|stage_unlock=' + flag('stage_unlock_mode', True))
        msgs.append('CONFIG|dual_character=' + flag('dual_character', False))
        msgs.append('CONFIG|character=' + self._character_number())
        msgs.append('CONFIG|time_trials=' + flag('include_time_trials', True))
        msgs.append('CONFIG|time_trial_mult=' + str(int(slot_data.get('time_trial_mult', 150))))
        msgs.append('CONFIG|cracked=' + flag('include_cracked', False))
        msgs.append('CONFIG|detonators=' + flag('include_detonators', True))
        msgs.append('CONFIG|pauls=' + flag('include_pauls', False))
        msgs.append('CONFIG|red_rooms=' + flag('include_red_rooms', False))
        msgs.append('CONFIG|coin_mult=' + str(int(slot_data.get('coin_multiplier', 100))))
        msgs.append('CONFIG|deathlink=' + flag('death_link', False))

        from worlds.antonblast.Locations import OPTION_KEY_TO_STAGE, STAGES
        display_to_key = {disp: key for disp, key in STAGES}
        start_display = OPTION_KEY_TO_STAGE.get(slot_data.get('starting_stage', 'boiler_city'), 'Boiler City')
        msgs.append('CONFIG|starting_stage=' + display_to_key.get(start_display, 'boilerCity'))

        msgs.append(self._session_message())
        return msgs

    def _character_number(self) -> str:
        char_val = (self.slot_data or {}).get('character', 0)
        if isinstance(char_val, str):
            return '1' if char_val.lower() == 'annie' else '0'

        return str(int(char_val))

    def _get_real_port(self) -> int:
        addr = getattr(self, 'server_address', '') or ''
        addr = addr.replace('wss://', '').replace('ws://', '').rstrip('/')
        if ':' in addr:
            try:
                return int(addr.rsplit(':', 1)[1])
            except ValueError:
                return DEFAULT_AP_PORT

        return DEFAULT_AP_PORT

    # config file shared with the game,
    # keeps archipelago_config in sync.
    def _update_config_file(self) -> None:
        slot_data = self.slot_data or {}
        try:
            import os

            config_dir = os.path.join(os.environ.get('LOCALAPPDATA', '.'), 'ANTONBLAST')
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, 'archipelago_config.txt')
            lines = ['archipelago.gg', str(DEFAULT_AP_PORT), '', '', '0', '0', '', '']

            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    lines = f.read().split('\n')
                while len(lines) < 8:
                    lines.append('')

            # never leave the connection lines in a state that crashes the game
            if not (lines[0] or '').strip():
                lines[0] = 'archipelago.gg'
            if not (lines[1] or '').strip().isdigit():
                lines[1] = str(DEFAULT_AP_PORT)

            lines[4] = '1' if slot_data.get('dual_character', False) else '0'
            lines[5] = self._character_number()
            lines[7] = str(getattr(self, 'seed_name', '') or '')

            with open(config_path, 'w') as f:
                f.write('\n'.join(lines[:8]) + '\n')
        except Exception as e:
            logger.warning(f'Failed to update config file: {e}')

    # log filtering
    @staticmethod
    def _strip_ap_markup(text: str) -> str:
        text = re.sub(r'\{[^}]*\}', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        text = re.sub(r'#[0-9A-Fa-f]{6}', '', text)

        return text.strip()

    def _concerns_self(self, args: dict) -> bool:
        receiving = args.get('receiving')
        if receiving is not None and self.slot_concerns_self(receiving):
            return True

        item = args.get('item')
        item_player = getattr(item, 'player', None) if item is not None else None
        if item_player is not None and self.slot_concerns_self(item_player):
            return True

        return False

    def on_print(self, text: str) -> None:
        if text.lower().startswith('location checked:'):
            return

        super().on_print(text)

    def on_print_json(self, args: dict) -> None:
        msg_type = args.get('type', '')

        # forward item/hint lines that involve this slot to the HUD of the game
        if msg_type in ('ItemSend', 'ItemCheat', 'Hint'):
            super().on_print_json(args)
            try:
                if not self._concerns_self(args):
                    return

                raw = self.jsontotextparser(args.get('data', []))
                clean = self._strip_ap_markup(raw)
                clean = re.sub(r'\s*\([^)]*\)\s*$', '', clean).strip()

                if clean:
                    self.game_item_queue.append('MESSAGE|' + clean)
            except Exception:
                pass

            return

        try:
            text = self.jsontotextparser(args.get('data', []))
            if self._strip_ap_markup(text).lower().startswith('location checked:'):
                return

        except Exception:
            pass

        super().on_print_json(args)

    def run_gui(self) -> None:
        from kvui import GameManager

        class AntonblastManager(GameManager):
            logging_pairs = [('Client', 'Archipelago'), ('Antonblast', 'Game')]
            base_title = 'Archipelago Antonblast Client'

        self.ui = AntonblastManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name='UI')

# game message handlers (called from the HTTP server)
async def _handle_poll(ctx: AntonblastContext, msg: str) -> None:
    ctx.last_poll_time = time.monotonic()

    # PING = the game just re-connected, redo the whole handshake
    if msg == 'PING' or not ctx.game_connected:
        ctx.config_sent = False
        ctx._disconnect_notified = False

    ctx.game_connected = True
    ctx._update_config_file()

    if not ctx.config_sent:
        ctx.config_sent = True
        for cfg in ctx._build_config_messages():
            ctx.game_item_queue.append(cfg)

        for scout_msg in ctx.scout_cache:
            ctx.game_item_queue.append(scout_msg)

        for checked_msg in ctx.checked_cache:
            ctx.game_item_queue.append(checked_msg)

async def _handle_location(ctx: AntonblastContext, msg: str) -> None:
    try:
        loc_id = int(msg.split('|', 1)[1])

        if loc_id not in ctx.locations_checked and loc_id not in ctx.checked_locations:
            ctx.locations_checked.add(loc_id)
            await ctx.send_msgs([{'cmd': 'LocationChecks', 'locations': [loc_id]}])

        from worlds.antonblast.Locations import LOC_OFFSET

        # the Satan goal location completes the slot
        if loc_id == LOC_OFFSET + 500 and not getattr(ctx, 'finished_game', False):
            ctx.finished_game = True
            from NetUtils import ClientStatus

            await ctx.send_msgs([{'cmd': 'StatusUpdate', 'status': ClientStatus.CLIENT_GOAL}])
            await ctx.send_msgs([{'cmd': 'Say', 'text': '!release'}])

            ctx.game_item_queue.append('MESSAGE|You beated Satan - AP Completed!')
    except Exception as e:
        logger.error('Location check error: ' + str(e))

async def _handle_death(ctx: AntonblastContext, msg: str) -> None:
    if 'DeathLink' in ctx.tags:
        await ctx.send_death(msg.split('|', 1)[1])

# Replays every item from the requested index so the game can catch up
# after a disconnect or a fresh/deleted save.
async def _handle_resync(ctx: AntonblastContext, msg: str) -> None:
    try:
        start = int(msg.split('|', 1)[1])
    except ValueError:
        start = 0

    for i in range(max(start, 0), len(ctx.items_received)):
        ctx.game_item_queue.append(ctx._item_message(ctx.items_received[i], i))

# local HTTP server
async def handle_http_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, ctx: AntonblastContext) -> None:
    try:
        await reader.readline()
        headers: dict[str, str] = {}

        while True:
            line = (await reader.readline()).decode(errors='replace').strip()
            if not line:
                break
                
            k, _, v = line.partition(':')
            headers[k.strip().lower()] = v.strip()

        body = b''
        if 'content-length' in headers:
            body = await reader.read(int(headers['content-length']))

        msg = body.decode('utf-8', errors='replace').strip()

        # not connected to the archipelago yet, tell the game to wait
        if ctx.slot is None:
            if msg in ('PING', 'POLL') and not ctx.game_connected:
                ctx.game_connected = True

            writer.write(b'HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
            await writer.drain()

            return

        if msg in ('PING', 'POLL'):
            await _handle_poll(ctx, msg)
        elif msg.startswith('LOCATION|'):
            await _handle_location(ctx, msg)
        elif msg.startswith('DEATH|'):
            await _handle_death(ctx, msg)
        elif msg.startswith('RESYNC|'):
            await _handle_resync(ctx, msg)

        # every response carries whatever is queued for the game
        items: list[str] = []
        while ctx.game_item_queue:
            items.append(ctx.game_item_queue.popleft())

        response_body = '\n'.join(items) + '\n' if items else 'OK\n'
        resp_bytes = response_body.encode()
        response = (
            'HTTP/1.1 200 OK\r\n'
            'Content-Length: ' + str(len(resp_bytes)) + '\r\n'
            'Content-Type: text/plain\r\n'
            'Connection: close\r\n\r\n'
        )
        writer.write(response.encode() + resp_bytes)

        await writer.drain()
    except Exception as e:
        logger.error('HTTP handler error: ' + str(e))
    finally:
        writer.close()


async def http_server_loop(ctx: AntonblastContext, port: int) -> None:
    server = None

    # retry the bind for a while: a leftover client process may still hold the port
    for attempt in range(30):
        try:
            server = await asyncio.start_server(
                lambda r, w: handle_http_request(r, w, ctx),
                '127.0.0.1', port,
            )
            break
        except OSError:
            if attempt == 0:
                logger.error('Port ' + str(port) + ' is already in use! Another Antonblast Client is probably still running.')
                logger.error('Close every other Antonblast Client window - retrying automatically...')

            await asyncio.sleep(2)

    if server is None:
        logger.error('Could not open port ' + str(port) + ' after 60 seconds. The game will NOT connect. Close other clients and restart this one.')
        return

    logger.info('HTTP server listening on 127.0.0.1:' + str(port) + ' - waiting for game')

    async with server:
        await server.serve_forever()

# Marks the game as disconnected when polls stop coming in.
async def game_watchdog_loop(ctx: AntonblastContext, timeout: float = GAME_TIMEOUT_SECONDS) -> None:
    await asyncio.sleep(5)

    while not ctx.exit_event.is_set():
        await asyncio.sleep(2)

        if ctx.game_connected and ctx.last_poll_time > 0:
            if time.monotonic() - ctx.last_poll_time > timeout:
                ctx.game_connected = False
                ctx.config_sent = False

                if not ctx._disconnect_notified:
                    ctx._disconnect_notified = True
                    logger.info('Antonblast game disconnected (no response)')

# entry point
async def run_client(launch_args: list[str]) -> None:
    parser = get_base_parser()
    parser.add_argument('--port', default=DEFAULT_HTTP_PORT, type=int, help=f'Local HTTP port for game IPC (default: {DEFAULT_HTTP_PORT})')
    args = parser.parse_args(launch_args)

    ctx = AntonblastContext(args.connect, args.password)
    logger.info('Starting Antonblast client')

    if ctx.server_task is None:
        await ctx.connect()

    if gui_enabled:
        ctx.run_gui()

    ctx.run_cli()

    http_task = asyncio.create_task(http_server_loop(ctx, args.port), name='HTTPServer')
    asyncio.create_task(game_watchdog_loop(ctx), name='GameWatchdog')

    await ctx.exit_event.wait()
    http_task.cancel()

    await ctx.shutdown()

def launch(*args: str) -> None:
    asyncio.run(run_client(list(args)))