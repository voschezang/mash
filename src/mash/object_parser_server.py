from flask import Flask, request

from examples.object_parser import Organization

basepath = '/v1/'


def init():
    app = Flask(__name__)
    init_routes(app)
    return app


def init_routes(app):
    @app.route(basepath + 'organizations', methods=['POST'])
    def organization():
        json = request.get_json()
        return str(Organization(json))

    @app.route(basepath + 'departments', methods=['POST'])
    def department():
        json = request.get_json()
        return str(organization(json))


if __name__ == "__main__":
    app = init()
    app.run()
