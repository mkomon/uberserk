# -*- coding: utf-8 -*-

import myurequests as requests
import urllib.parse

from . import models
from . import exceptions
from .formats import JSON, TEXT

# Base URL for the API
API_URL = 'https://lichess.org/'

__all__ = [
    'Account',
    'Board',
    'Games',
    'Users',
    'Teams',
]


class BaseClient:
    def __init__(self, auth_token, base_url=None):
        self._r = Requestor(auth_token, base_url or API_URL, default_fmt=JSON)


class Client(BaseClient):
    def __init__(self, auth_token, base_url=None, pgn_as_default=False):
        super().__init__(auth_token, base_url)
        self.account = Account(auth_token, base_url)
        self.games = Games(auth_token, base_url)
        self.board = Board(auth_token, base_url)
        self.users = Users(auth_token, base_url)
        self.teams = Teams(auth_token, base_url)


def noop(arg):
    return arg


class Requestor:
    def __init__(self, auth_token=None, base_url=None, default_fmt=JSON):
        self.base_url = base_url
        self.auth_token = auth_token
        self.default_fmt = default_fmt

    def request(self, method, path, *args, fmt=None, converter=noop, **kwargs):
        """Make a request for a resource in a paticular format.
        :param str method: HTTP verb
        :param str path: the URL suffix
        :param fmt: the format handler
        :type fmt: :class:`~berserk.formats.FormatHandler`
        :param func converter: function to handle field conversions
        :return: response
        :raises berserk.exceptions.ResponseError: if the status is >=400
        """
        fmt = fmt or self.default_fmt
        kwargs['headers'] = {'Authorization': 'Bearer {}'.format(self.auth_token)}
        url = urllib.parse.urljoin(self.base_url, path)
        if 'params' in kwargs:
            url = url.rstrip('?') + '?' + urllib.parse.urlencode(kwargs['params'], doseq=True)
            kwargs.pop('params')

        is_stream = kwargs.get('stream')
        print('%s %s %s params=%s data=%s json=%s',
                  'stream' if is_stream else 'request', method, url,
                  kwargs.get('params'), kwargs.get('data'), kwargs.get('json'))
        try:
            response = requests.request(method, url, *args, **kwargs)
        except Exception as e:
            raise exceptions.ApiError(e)
        # print('dir(response): %s' % dir(response))
        # print('response.status_code: %s' % response.status_code)
        # print('response.text: %s' % response.text)
        if response.status_code != 200:
            raise exceptions.ResponseError(response)

        return fmt.handle(response, is_stream=is_stream, converter=converter)

    def get(self, *args, **kwargs):
        """Convenience method to make a GET request."""
        return self.request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        """Convenience method to make a POST request."""
        return self.request('POST', *args, **kwargs)


class Account(BaseClient):
    def get(self):
        """Get your public information.
        :return: public information about the authenticated user
        :rtype: dict
        """
        path = 'api/account'
        return self._r.get(path, converter=models.Account.convert)

    def get_preferences(self):
        """Get your account preferences.
        :return: preferences of the authenticated user
        :rtype: dict
        """
        path = 'api/account/preferences'
        return self._r.get(path)['prefs']

class Games(BaseClient):
    """Client for games-related endpoints."""

    # move this to Account?
    def get_ongoing(self, count=10):
        """Get your currently ongoing games.
        :param int count: number of games to get
        :return: some number of currently ongoing games
        :rtype: list
        """
        path = 'api/account/playing'
        params = {'nb': count}
        return self._r.get(path, params=params)['nowPlaying']

class Board(BaseClient):
    """Client for physical board or external application endpoints."""

    def stream_incoming_events(self):
        """Get your realtime stream of incoming events.
        :return: stream of incoming events
        :rtype: iterator over the stream of events
        """
        path = 'api/stream/event'
        yield from self._r.get(path, stream=True)

    def seek(self, time, increment, rated=False, variant='standard',
             color='random', rating_range=None):
        """Create a public seek to start a game with a random opponent.
        :param int time: intial clock time in minutes
        :param int increment: clock increment in minutes
        :param bool rated: whether the game is rated (impacts ratings)
        :param str variant: game variant to use
        :param str color: color to play
        :param rating_range: range of opponent ratings
        :return: duration of the seek
        :rtype: float
        """
        if isinstance(rating_range, (list, tuple)):
            low, high = rating_range
            rating_range = '%s-%s' % (low, high)

        path = '/api/board/seek'
        payload = {
            'rated': str(bool(rated)).lower(),
            'time': time,
            'increment': increment,
            'variant': variant,
            'color': color,
            'ratingRange': rating_range or '',
        }

        # we time the seek
        start = now()

        # just keep reading to keep the search going
        for line in self._r.post(path, data=payload, fmt=TEXT, stream=True):
            pass

        # and return the time elapsed
        return now() - start

    def stream_game_state(self, game_id):
        """Get the stream of events for a board game.
        :param str game_id: ID of a game
        :return: iterator over game states
        """
        path = 'api/board/game/stream/%s' % game_id
        yield from self._r.get(path, stream=True,
                               converter=models.GameState.convert)

    def make_move(self, game_id, move):
        """Make a move in a board game.
        :param str game_id: ID of a game
        :param str move: move to make
        :return: success
        :rtype: bool
        """
        path = 'api/board/game/%s/move/%s' % (game_id, move)
        return self._r.post(path)['ok']

    def post_message(self, game_id, text, spectator=False):
        """Post a message in a board game.
        :param str game_id: ID of a game
        :param str text: text of the message
        :param bool spectator: post to spectator room (else player room)
        :return: success
        :rtype: bool
        """
        path = 'api/board/game/%s/chat' % game_id
        room = 'spectator' if spectator else 'player'
        payload = {'room': room, 'text': text}
        return self._r.post(path, json=payload)['ok']

    def abort_game(self, game_id):
        """Abort a board game.
        :param str game_id: ID of a game
        :return: success
        :rtype: bool
        """
        path = 'api/board/game/%s/abort' % game_id
        return self._r.post(path)['ok']

    def resign_game(self, game_id):
        """Resign a board game.
        :param str game_id: ID of a game
        :return: success
        :rtype: bool
        """
        path = 'api/board/game/%s/resign' % game_id
        return self._r.post(path)['ok']

    def handle_draw_offer(self, game_id, accept):
        """Create, accept, or decline a draw offer.
        To offer a draw, pass ``accept=True`` and a game ID of an in-progress
        game. To response to a draw offer, pass either ``accept=True`` or
        ``accept=False`` and the ID of a game in which you have recieved a
        draw offer.
        Often, it's easier to call :func:`offer_draw`, :func:`accept_draw`, or
        :func:`decline_draw`.
        :param str game_id: ID of an in-progress game
        :param bool accept: whether to accept
        :return: True if successful
        :rtype: bool
        """
        accept = "yes" if accept else "no"
        path = '/api/board/game/%s/draw/%s' % (game_id, accept)
        return self._r.post(path)['ok']

    def offer_draw(self, game_id):
        """Offer a draw in the given game.
        :param str game_id: ID of an in-progress game
        :return: True if successful
        :rtype: bool
        """
        return self.handle_draw_offer(game_id, True)

    def accept_draw(self, game_id):
        """Accept an already offered draw in the given game.
        :param str game_id: ID of an in-progress game
        :return: True if successful
        :rtype: bool
        """
        return self.handle_draw_offer(game_id, True)

    def decline_draw(self, game_id):
        """Decline an already offered draw in the given game.
        :param str game_id: ID of an in-progress game
        :return: True if successful
        :rtype: bool
        """
        return self.handle_draw_offer(game_id, False)


class Users(BaseClient):
    """Client for user-related endpoints."""

    def get_realtime_statuses(self, *user_ids):
        """Get the online, playing, and streaming statuses of players.

        Only id and name fields are returned for offline users.

        :param user_ids: one or more user IDs (names)
        :return: statuses of given players
        :rtype: list
        """
        path = 'api/users/status'
        params = {'ids': ','.join(user_ids)}
        return self._r.get(path, params=params)

    def get_all_top_10(self):
        """Get the top 10 players for each speed and variant.

        :return: top 10 players in each speed and variant
        :rtype: dict
        """
        path = 'player'
        return self._r.get(path, fmt=JSON)

    def get_leaderboard(self, perf_type, count=10):
        """Get the leaderboard for one speed or variant.

        :param perf_type: speed or variant
        :type perf_type: :class:`~berserk.enums.PerfType`
        :param int count: number of players to get
        :return: top players for one speed or variant
        :rtype: list
        """
        path = 'player/top/%s/%s' % (count, perf_type)
        return self._r.get(path, fmt=JSON)['users']

    def get_public_data(self, username):
        """Get the public data for a user.

        :param str username: username
        :return: public data available for the given user
        :rtype: dict
        """
        path = 'api/user/%s' % username
        return self._r.get(path, converter=models.User.convert)

    def get_activity_feed(self, username):
        """Get the activity feed of a user.

        :param str username: username
        :return: activity feed of the given user
        :rtype: list
        """
        path = 'api/user/%s/activity' % username
        return self._r.get(path, converter=models.Activity.convert)

    def get_by_id(self, *usernames):
        """Get multiple users by their IDs.

        :param usernames: one or more usernames
        :return: user data for the given usernames
        :rtype: list
        """
        path = 'api/users'
        return self._r.post(path, data=','.join(usernames),
                            converter=models.User.convert)

    def get_live_streamers(self):
        """Get basic information about currently streaming users.

        :return: users currently streaming a game
        :rtype: list
        """
        path = 'streamer/live'
        return self._r.get(path)

    def get_users_followed(self, username):
        """Stream users followed by a user.

        :param str username: a username
        :return: iterator over the users the given user follows
        :rtype: iter
        """
        path = '/api/user/%s/following' % username
        return self._r.get(path, stream=True, fmt=JSON,
                           converter=models.User.convert)

    def get_users_following(self, username):
        """Stream users who follow a user.

        :param str username: a username
        :return: iterator over the users that follow the given user
        :rtype: iter
        """
        path = '/api/user/%s/followers' % username
        return self._r.get(path, stream=True, fmt=JSON,
                           converter=models.User.convert)

    def get_rating_history(self, username):
        """Get the rating history of a user.

        :param str username: a username
        :return: rating history for all game types
        :rtype: list
        """
        path = '/api/user/%s/rating-history' % username
        return self._r.get(path, converter=models.RatingHistory.convert)


class Teams(BaseClient):

    def get_members(self, team_id):
        """Get members of a team.

        :param str team_id: ID of a team
        :return: users on the given team
        :rtype: iter
        """
        path = 'team/%s/users' % team_id
        return self._r.get(path, fmt=JSON, stream=True,
                           converter=models.User.convert)

    def join(self, team_id):
        """Join a team.

        :param str team_id: ID of a team
        :return: success
        :rtype: bool
        """
        path = '/team/%s/join' % team_id
        return self._r.post(path)['ok']

    def leave(self, team_id):
        """Leave a team.

        :param str team_id: ID of a team
        :return: success
        :rtype: bool
        """
        path = '/team/%s/quit' % team_id
        return self._r.post(path)['ok']

    def kick_member(self, team_id, user_id):
        """Kick a member out of your team.

        :param str team_id: ID of a team
        :param str user_id: ID of a team member
        :return: success
        :rtype: bool
        """
        path = '/team/%s/kick/%s' % (team_id, user_id)
        return self._r.post(path)['ok']
