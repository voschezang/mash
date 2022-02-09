from flask import Flask, request
import numpy as np
import time
from http import HTTPStatus

basepath = '/v1/'


def init():
    app = Flask(__name__)
    init_routes(app)
    return app


def init_routes(app):
    @app.route(basepath + "stable")
    def stable():
        return 'ok'

    @app.route(basepath + "scrambled")
    def scrambled():
        time.sleep(np.random.lognormal(0, sigma=1))
        return 'ok'

    @app.route(basepath + "noisy")
    def noisy():
        eta = np.random.random()
        if eta < 1/3.:
            return 'ok'
        if eta < 2/3.:
            return '', HTTPStatus.SERVICE_UNAVAILABLE
        return '', HTTPStatus.GATEWAY_TIMEOUT

    @app.route(basepath + "echo", methods=['GET', 'POST'])
    def echo():
        json = request.get_json()
        args = request.args.items()
        if json is None:
            json = {}

        if isinstance(json, dict):
            # merge json with url params if possible
            json.update(args)

        return json

    @app.route(basepath + "document", methods=['POST'])
    def create_document():
        json = request.get_json()
        return json.keys()


if __name__ == "__main__":
    app = init()
    app.run()
