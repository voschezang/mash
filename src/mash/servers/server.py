from flask import Flask
import os

from mash.servers.adapters.api.document_routes import document_routes
from mash.servers.adapters.api.standard_routes import standard_routes
from mash.servers.adapters.api.user_routes import user_routes
from mash.servers.adapters.repository import UPLOAD_FOLDER, init_db


def init():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    init_routes(app)
    return app


def init_routes(app):
    standard_routes(app)
    document_routes(app)
    user_routes(app)


if __name__ == "__main__":
    app = init()
    app.run()
