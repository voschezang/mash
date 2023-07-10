from flask import request
from http import HTTPStatus
import numpy as np
import time

from mash.servers_extra import verify_server
from mash.servers.repository import basepath


def init(app):
    @app.route(basepath)
    def root():
        data = ['documents', 'users']
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
