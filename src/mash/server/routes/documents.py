from json import JSONDecodeError, loads
from logging import debug
from flask import request
from http import HTTPStatus
from werkzeug.utils import secure_filename
import os


from mash.server.domain.css import Document
from mash.object_parser.errors import BuildError, BuildErrors, to_string
from mash.object_parser import build
from mash.server.repository import UPLOAD_FOLDER
from mash.server.routes.default import basepath


def init(app):
    @app.route(basepath + 'documents', methods=['POST'])
    def documents_create():
        print(request.files)
        try:
            file = request.files['file']
        except KeyError:
            return 'Invalid Payload', HTTPStatus.BAD_REQUEST

        fn = secure_filename(file.filename)
        file.save(UPLOAD_FOLDER + '/' + fn)

        return f'file {fn} saved', HTTPStatus.CREATED

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
