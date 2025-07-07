#!/usr/bin/python3
"""A webserver
"""
from flask_cors import CORS

if __name__ == '__main__':
    import _extend_path  # noqa

from mash.server.server import init

if __name__ == "__main__":
    app = init()
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    app.run(debug=True)
