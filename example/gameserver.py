#!/usr/bin/env python3

from flask import Flask, jsonify, request, abort

class ApiSession:

    CREDENTIALS = {
        'markku': '3l1t3',
        'guest':  'lam3'
    }

    def __init__(self):
        self._sessions = {}

    def login(self, user, passw):
        if user in self.CREDENTIALS:
            exp_pass = self.CREDENTIALS[user]
            if passw == exp_pass:
                token = self._new_session(user)
                return token
        print("login failed")
        return None

    def logout(self, token):
        del self._sessions[token]

    def get_session(self, request):
        if "token" not in request.args:
            return None

        token = request.args["token"]
        if token not in self._sessions:
            return None

        return self._sessions[token]

    def _new_session(self, user):
        with open("/dev/urandom", "rb") as f:
            rnd = f.read(16)
        token = rnd.hex()
        self._sessions[token] = {"user": user, "token": token}
        return token
        # todo session expiry


class Player:

    def __init__(self, user, alias):
        self._user = user
        self._alias = alias

    def get_user(self):
        return self._user

    def get_alias(self):
        return self._alias


class GameLobby:
    def __init__(self):
        self._pending_players = {}

    def register(self, user, alias):
        if user not in self._pending_players:
            player = Player(user, alias)
            self._pending_players[user] = player
            return True
        else:
            return False

    def unregister(self, user):
        if user in self._pending_players:
            del self._pending_players[user]
            return True
        else:
            return False

    def list_players(self):
        ret = []
        for k, v in self._pending_players.items:
            ret.append(v.get_alias())
        return ret


app = Flask(__name__)
app.api_session = ApiSession()
app.lobby = GameLobby()


def get_api_session():
    return app.api_session


def get_lobby():
    return app.lobby


@app.route('/game/login', methods=["POST"])
def login():
    """ log into the game lobby """
    user = request.args['user'] if 'user' in request.args else ''
    passw = request.args['pass'] if 'pass' in request.args else ''

    token = get_api_session().login(user, passw)
    if token:
        return jsonify({'status': 'OK', 'token': token})
    print("bad login")
    abort(401)


@app.route('/game/logout', methods=["POST"])
def logout():
    """ log out and forget about the user """
    session = get_api_session().get_session(request)
    if not session:
        abort(401)

    get_lobby().unregister(session['user'])
    get_api_session().logout(session['token'])

    return jsonify({'status': 'OK'})


@app.route("/game/register", methods=["POST"])
def register():
    """ register caller into game lobby as a player candidate"""

    session = get_api_session().get_session(request)
    if not session:
        abort(401)

    user = session['user']
    alias = request.args['alias'] if 'alias' in request.args else user

    lobby = get_lobby()
    if not lobby.register(user, alias):
        abort(400)
    return jsonify({'status': 'OK'})


@app.route("/game/unregister", methods=["POST"])
def unregister():
    """ unregister as a player candidate"""

    session = get_api_session().get_session(request)
    if not session:
        abort(401)

    user = session['user']
    lobby = get_lobby()
    if not lobby.unregister(user):
        abort(400)
    return jsonify({'status': 'OK'})


if __name__ == '__main__':
    app.run(debug=True)
