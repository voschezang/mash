from json import JSONDecodeError, loads
from logging import debug
from flask import request
from http import HTTPStatus
from werkzeug.utils import secure_filename
import numpy as np
import os
import time


from mash.servers import verify_server
from mash.servers.css import Document
from mash.object_parser.errors import BuildError, BuildErrors, to_string
from mash.object_parser import build
from mash.servers.config import RawUser, basepath, UPLOAD_FOLDER, create_user, get_db


from mash.servers.config import basepath, db


def init_routes(app):
    @app.route(basepath)
    def root():
        data = ['document', 'users']
        test = ['echo', 'sleep', 'stable', 'scrambled', 'noisy']
        return data + test

    @app.route(basepath + "echo", methods=['GET', 'POST'])
    def echo():
        json = request.get_json()
        args = request.args.items()
        if json is None:
            json = {}

        if isinstance(json, dict):
            # merge json with url params if possible
            json.update(args)
        elif not isinstance(json, str):
            return str(json)

        return json

    @app.route(basepath + 'stable')
    def stable():
        return 'ok'

    @app.route(basepath + 'scrambled')
    def scrambled():
        time.sleep(np.random.lognormal(0, sigma=1))
        return 'ok'

    @app.route(basepath + 'noisy')
    def noisy():
        eta = np.random.random()
        if eta < 1/3.:
            return 'ok'
        if eta < 2/3.:
            return '', HTTPStatus.SERVICE_UNAVAILABLE
        return '', HTTPStatus.GATEWAY_TIMEOUT

    @app.route(basepath + 'sleep')
    def sleep():
        if 'time' in request.args:
            t = request.args['time']
            time.sleep(float(t))
            return 'ok'

        return '', HTTPStatus.BAD_REQUEST

    @app.route(basepath + 'documents', methods=['POST'])
    def documents_create():
        print(request.files)
        try:
            file = request.files['file']
        except KeyError:
            return 'Invalid Payload', HTTPStatus.BAD_REQUEST

        fn = secure_filename(file.filename)
        file.save(UPLOAD_FOLDER + '/' + fn)

        return f'file {fn} was saved', HTTPStatus.CREATED

    @app.route(basepath + 'documents', methods=['DELETE'])
    def documents_delete():
        for fn in os.listdir(UPLOAD_FOLDER):
            try:
                os.remove(UPLOAD_FOLDER + '/' + fn)
            except (IsADirectoryError, PermissionError):
                # ignore folders
                continue

        return 'ok'

    @app.route(basepath + 'documents/<id>/style', methods=['PUT'])
    def documents_style_update(id):
        if id not in ['1', '2', '3']:
            return f'Invalid document id', HTTPStatus.BAD_REQUEST

        path = f'/documents/{id}/style'

        try:
            data = loads(request.data)
        except JSONDecodeError as e:
            debug(f'POST {path}: JSONDecodeError: {e}')
            return 'Payload decoding error', HTTPStatus.BAD_REQUEST

        # WARNING: this exposes internal classes
        try:
            obj = build(Document, data)
        except BuildError as e:
            debug(f'POST {path}\n' + e.args[0])
            return f'Invalid input: {e.args[0]}', HTTPStatus.BAD_REQUEST
        except BuildErrors as e:
            errors = to_string(e)
            debug(f'POST {path}\n' + errors)
            return f'Invalid input: {errors}', HTTPStatus.BAD_REQUEST

        return {'id': 1, 'data': str(obj)}

    @app.route(basepath + 'server/verify', methods=['POST'])
    def verify_target_server():
        if 'URL' not in request.args:
            return '', HTTPStatus.BAD_REQUEST

        url = request.args['URL']

        try:
            success, msg = verify_server.main(url)
        except ValueError:
            return 'Invalid URL', HTTPStatus.BAD_REQUEST

        return {'success': success, 'msg': msg}

    @app.route(basepath + 'users', methods=['GET', 'POST'])
    def users():
        if request.method == 'GET':
            return [i for i in get_db()['users'].keys()]

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

        if id in get_db()['users']:
            return get_db()['users'][id]

        return '', HTTPStatus.NOT_FOUND
