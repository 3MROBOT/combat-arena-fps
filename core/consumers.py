import json
import uuid

from channels.generic.websocket import AsyncWebsocketConsumer

# ---------------------------------------------------------------------------
# In-memory room registry, shared by every consumer instance in this process.
#
# This project runs as a single Daphne process on one machine for a LAN
# game, so a plain dict living in process memory is a valid, fast,
# server-authoritative source of truth for room/team/round state. It resets
# if the server restarts - acceptable for this use case.
#
# ROOMS[room_name] = {
#     'players': { player_id: {'name','team','alive','health'} },
#     'round_state': 'lobby' | 'playing' | 'round_over',
#     'round_number': int,
# }
# ---------------------------------------------------------------------------
ROOMS = {}

MAX_HEALTH = 150

SPAWN_POINTS = {
    'yar': [(-32, 32), (-40, 18), (-24, 42), (-44, 4), (-28, -10), (-38, -22)],
    'enemy': [(32, -32), (40, -18), (24, -42), (44, -4), (28, 10), (38, 22)],
}


def get_room(room_name):
    if room_name not in ROOMS:
        ROOMS[room_name] = {'players': {}, 'round_state': 'lobby', 'round_number': 0}
    return ROOMS[room_name]


def room_state_payload(room):
    """The full, authoritative snapshot of a room. Sent on join AND on every
    periodic re-sync request, so a client that missed an earlier event (a
    join, a team change, a position tick) always self-heals within one
    sync cycle instead of staying permanently out of date."""
    return {
        'type': 'room_state',
        'round_state': room['round_state'],
        'round_number': room['round_number'],
        'players': [
            {
                'id': pid, 'name': p['name'], 'team': p['team'], 'alive': p['alive'],
                'x': p.get('x', 0), 'y': p.get('y', 0), 'z': p.get('z', 0), 'yaw': p.get('yaw', 0),
            }
            for pid, p in room['players'].items()
        ],
    }


def team_counts(room):
    counts = {'yar': 0, 'enemy': 0}
    for p in room['players'].values():
        if p['team'] in counts:
            counts[p['team']] += 1
    return counts


def spawn_for(room, player_id):
    player = room['players'].get(player_id)
    team = player['team'] if player else None
    points = SPAWN_POINTS.get(team, [(0, 0)])
    ids_on_team = [pid for pid, p in room['players'].items() if p['team'] == team]
    try:
        idx = ids_on_team.index(player_id) % len(points)
    except ValueError:
        idx = 0
    return points[idx]


class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = f'game_{self.room_name}'
        self.player_id = uuid.uuid4().hex[:8]

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'your_id': self.player_id,
        }))

    async def disconnect(self, close_code):
        room = ROOMS.get(self.room_name)
        if room and self.player_id in room['players']:
            del room['players'][self.player_id]
            await self.broadcast({'type': 'player_left', 'id': self.player_id})
            await self.maybe_end_round(room)

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except ValueError:
            return

        msg_type = data.get('type')
        room = get_room(self.room_name)

        if msg_type == 'join':
            await self.handle_join(room, data)
        elif msg_type == 'select_team':
            await self.handle_select_team(room, data)
        elif msg_type == 'start_game':
            await self.handle_start_game(room)
        elif msg_type == 'position':
            await self.handle_position(room, data)
        elif msg_type == 'hit_report':
            await self.handle_hit_report(room, data)
        elif msg_type == 'shot_fired':
            await self.broadcast({'type': 'shot_fired', 'id': self.player_id}, skip_self=True)
        elif msg_type == 'request_sync':
            await self.send(text_data=json.dumps(room_state_payload(room)))
        # unrecognized message types are dropped rather than trusted/broadcast blindly

    # ---- handlers -----------------------------------------------------

    async def handle_join(self, room, data):
        name = str(data.get('name', 'Player'))[:14] or 'Player'
        room['players'][self.player_id] = {'name': name, 'team': None, 'alive': True, 'health': MAX_HEALTH}

        await self.send(text_data=json.dumps(room_state_payload(room)))

        await self.broadcast({'type': 'player_joined', 'id': self.player_id, 'name': name}, skip_self=True)

    async def handle_select_team(self, room, data):
        team = data.get('team')
        if team not in ('yar', 'enemy'):
            return
        player = room['players'].get(self.player_id)
        if not player:
            return
        player['team'] = team
        await self.broadcast({
            'type': 'team_update',
            'id': self.player_id,
            'team': team,
            'counts': team_counts(room),
        })

    async def handle_start_game(self, room):
        if not room['players']:
            return
        room['round_state'] = 'playing'
        room['round_number'] += 1
        for p in room['players'].values():
            p['alive'] = True
            p['health'] = MAX_HEALTH
        spawns = {pid: spawn_for(room, pid) for pid in room['players']}
        for pid, (sx, sz) in spawns.items():
            room['players'][pid]['x'], room['players'][pid]['y'], room['players'][pid]['z'] = sx, 0, sz
        await self.broadcast({
            'type': 'round_start',
            'round_number': room['round_number'],
            'spawns': spawns,
        })

    async def handle_position(self, room, data):
        player = room['players'].get(self.player_id)
        if not player or not player['alive']:
            return
        x, y, z, yaw = data.get('x', 0), data.get('y', 0), data.get('z', 0), data.get('yaw', 0)
        player['x'], player['y'], player['z'], player['yaw'] = x, y, z, yaw
        await self.broadcast({
            'type': 'position', 'id': self.player_id, 'x': x, 'y': y, 'z': z, 'yaw': yaw,
        }, skip_self=True)

    async def handle_hit_report(self, room, data):
        shooter = room['players'].get(self.player_id)
        target_id = data.get('target_id')
        target = room['players'].get(target_id)
        if not shooter or not target or not shooter['alive'] or not target['alive']:
            return
        if shooter['team'] is None or shooter['team'] == target['team']:
            return  # only cross-team hits are valid

        damage = min(max(int(data.get('damage', 0)), 0), 40)
        target['health'] -= damage

        if target['health'] <= 0:
            target['health'] = 0
            target['alive'] = False
            await self.broadcast({'type': 'player_died', 'id': target_id, 'by': self.player_id})
            await self.maybe_end_round(room)
        else:
            await self.broadcast({'type': 'health_update', 'id': target_id, 'health': target['health']})

    async def maybe_end_round(self, room):
        """A round ends the moment one whole team has no one left alive.
        The surviving team wins. We do NOT auto-respawn here - everyone
        (winners included) sees a Round Over screen and stays in this same
        room; the round only restarts when someone clicks "play again",
        which sends 'start_game' again."""
        if room['round_state'] != 'playing':
            return

        team_alive = {'yar': 0, 'enemy': 0}
        team_total = {'yar': 0, 'enemy': 0}
        for p in room['players'].values():
            if p['team'] in team_alive:
                team_total[p['team']] += 1
                if p['alive']:
                    team_alive[p['team']] += 1

        teams_in_play = [t for t in ('yar', 'enemy') if team_total[t] > 0]
        if len(teams_in_play) < 2:
            return  # need both teams present to have a meaningful outcome

        eliminated = [t for t in teams_in_play if team_alive[t] == 0]
        if not eliminated:
            return

        winner = None
        if len(eliminated) == 1:
            other = 'enemy' if eliminated[0] == 'yar' else 'yar'
            if team_alive.get(other, 0) > 0:
                winner = other
        # if both teams got eliminated in the same instant, winner stays None (draw)

        room['round_state'] = 'round_over'
        await self.broadcast({'type': 'round_over', 'winner': winner})

    # ---- helpers --------------------------------------------------------

    async def broadcast(self, data, skip_self=False):
        payload = dict(data)
        payload['_skip'] = self.channel_name if skip_self else None
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'relay_message', 'sender_channel': self.channel_name, 'data': payload},
        )

    async def relay_message(self, event):
        data = dict(event['data'])
        skip_channel = data.pop('_skip', None)
        if skip_channel and skip_channel == self.channel_name:
            return
        await self.send(text_data=json.dumps(data))
