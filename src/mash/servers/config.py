from dataclasses import dataclass


UPLOAD_FOLDER = 'tmp/flask-app'

# Note the trailing `/`
basepath = '/v1/'
db = None


@dataclass
class RawUser:
    name: str
    email: str


def init_db():
    global db
    db = {'users': {i: generate_user(i) for i in range(10)}}


def get_db():
    global db
    return db


def url(path):
    return f'http://127.0.0.1:5000{basepath}{path}'


def generate_user(i: int) -> dict:
    return {'name': f'name_{i}', 'email': f'name.{i}@company.com'}


def create_user(user: RawUser):
    # generate user id
    id = len(db['users']) + 1
    # create object
    user = {'name': user.name, 'email': user.email}
    # store object
    db['users'][id] = user
    return id
