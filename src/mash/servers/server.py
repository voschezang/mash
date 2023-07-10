from flask import Flask
import os

from mash.servers.api import default, documents, users
from mash.servers.repository import UPLOAD_FOLDER, init_db
from mash.servers.model.user import init_users


def init():
    init_db()
    init_users()

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    init_routes(app)

    return app


def init_routes(app):
    default.init(app)
    documents.init(app)
    users.init(app)


if __name__ == "__main__":
    app = init()
    app.run()
