UPLOAD_FOLDER = 'tmp/flask-app'

db = None


class Repository:
    def __init__(self):
        global db
        db = {'users': {}}

    @staticmethod
    def read():
        return db


def create_user(name, email):
    # generate user id
    id = len(db['users']) + 1000
    # create object
    user = {'name': name, 'email': email}
    # store object
    db['users'][id] = user
    return id
