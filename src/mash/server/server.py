"""A dummy web server.

API endpoints

.. code-block:: yaml

    - /verify server
    - /users
    - /documents

The internal structure is decoupled.

.. code-block:: yaml

    - domain: Domain model
        - user.py # A domain object
    - routes: Exposed API methods
        - users.py # User-related routing
    - repository.py: Persistency layer

"""
from flask import Flask
import os

from mash.server.routes import default, documents, users
from mash.server.repository import UPLOAD_FOLDER, Repository
from mash.server.domain.user import init_users


def init():
    Repository()
    init_users()

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    app = Flask(__name__)

    # TODO use https://flask-restful.readthedocs.io/en/latest/index.html

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
