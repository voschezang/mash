from flask import Flask
import os

from mash.servers.css import Document
from mash.object_parser.errors import BuildError, BuildErrors, to_string
from mash.object_parser import build
from mash.servers.config import basepath, UPLOAD_FOLDER, init_db
from mash.servers.routes import init_routes


def init():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    init_routes(app)
    return app


if __name__ == "__main__":
    app = init()
    app.run()
