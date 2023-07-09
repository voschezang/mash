from mash.servers.model.user import RawUser


UPLOAD_FOLDER = 'tmp/flask-app'

# Note the trailing `/`
basepath = '/v1/'
db = None


def init_db():
    global db
    db = {'users': {}}
    for i in range(10):
        user = generate_user(i)
        create_user(user)


def read():
    global db
    return db


def url(path):
    return f'http://127.0.0.1:5000{basepath}{path}'


def generate_user(i: int) -> RawUser:
    return RawUser(f'name_{i}', f'name.{i}@company.com')


def create_user(user: RawUser):
    # generate user id
    id = len(db['users']) + 1000
    # create object
    user = {'name': user.name, 'email': user.email}
    # store object
    db['users'][id] = user
    return id
