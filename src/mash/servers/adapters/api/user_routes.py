from json import JSONDecodeError, loads
from logging import debug
from flask import request
from http import HTTPStatus


from mash.object_parser.errors import BuildError, BuildErrors, to_string
from mash.object_parser import build
from mash.servers.model.user import RawUser
from mash.servers.adapters.repository import basepath, create_user, read


def user_routes(app):
    @app.route(basepath + 'users', methods=['GET', 'POST'])
    def users():
        if request.method == 'GET':
            return [i for i in read()['users'].keys()]

        if request.method == 'POST':
            try:
                data = loads(request.data)
            except JSONDecodeError:
                return 'Payload decoding error', HTTPStatus.BAD_REQUEST

            # WARNING: this exposes internal classes
            try:
                user = build(RawUser, data)
            except BuildError as e:
                debug('POST /users\n' + e.args[0])
                return f'Invalid input: {e.args[0]}', HTTPStatus.BAD_REQUEST
            except BuildErrors as e:
                errors = to_string(e)
                debug('POST /users\n' + errors)
                return f'Invalid input: {errors}', HTTPStatus.BAD_REQUEST

            id = create_user(user)
            return str(id), HTTPStatus.CREATED

        return '', HTTPStatus.BAD_REQUEST

    @app.route(basepath + 'users/<id>')
    def users_user(id):
        try:
            id = int(id)
        except TypeError:
            return 'Invalid user id', HTTPStatus.BAD_REQUEST

        users = read()['users']
        if id in users:
            return users[id]

        return '', HTTPStatus.NOT_FOUND
