from flask import Flask, Response
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


if __name__ == "__main__":
    app = init()
    app.run()
