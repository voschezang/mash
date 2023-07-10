
UPLOAD_FOLDER = 'tmp/flask-app'

db = None


def init_db():
    global db
    db = {'users': {}}


def read():
    global db
    return db


def create_user(name, email):
    # generate user id
    id = len(db['users']) + 1000
    # create object
    user = {'name': name, 'email': email}
    # store object
    db['users'][id] = user
    return id
