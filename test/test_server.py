import json
from flask.testing import FlaskClient
import os
from io import BytesIO
from http import HTTPStatus

from mash.server.repository import UPLOAD_FOLDER
from mash.server.routes.default import basepath
from mash.server.server import init as init_server

LARGE_N = 1000


def test_route_stable_simple():
    client = init()
    response = client.get(basepath + 'stable')
    assert_response(response)


def test_route_stable():
    url = basepath + 'stable'
    responses = requests(url, N=5)
    assert all(verify_response(r, expected_data=b'ok')
               for r in responses)


def test_route_sleep():
    url = basepath + 'sleep?time=0.0001'
    responses = requests(url, N=5)
    responses = list(responses)
    print(responses[0].get_data())
    assert all(verify_response(r, expected_data=b'ok')
               for r in responses)


def test_route_sleep_without_args():
    url = basepath + 'sleep'
    responses = requests(url, N=5)
    assert all(verify_response(r, expected_status=HTTPStatus.BAD_REQUEST)
               for r in responses)


def test_route_scrambled():
    url = basepath + 'scrambled'
    responses = requests(url)
    assert any(verify_response(r) for r in responses)


def test_route_noisy_happy_flow():
    url = basepath + 'noisy'
    responses = requests(url)
    assert any(verify_response(r) for r in responses)


def test_route_noisy_bad_flow():
    url = basepath + 'noisy'
    responses = requests(url)

    assert any(verify_response(r, HTTPStatus.SERVICE_UNAVAILABLE)
               for r in responses)

    assert any(verify_response(r, HTTPStatus.GATEWAY_TIMEOUT)
               for r in responses)


def test_route_echo():
    url = basepath + 'echo'
    json = 'this could be json'
    responses = requests(url, N=5, json=json)
    assert all(verify_response(r, expected_data=json.encode())
               for r in responses)


def test_route_echo_int():
    json = 123
    url = basepath + 'echo'
    responses = requests(url, N=5, json=json)
    assert all(verify_response(r, expected_data=str(json).encode())
               for r in responses)


def test_document_post():
    client = init()
    fn = 'myfile.txt'
    out_fn = UPLOAD_FOLDER + '/' + fn
    try:
        os.remove(out_fn)
    except FileNotFoundError:
        pass

    body = b'abc'
    expected_data = f'file {fn} saved'
    file = (BytesIO(body), fn)
    res = client.post(basepath + 'documents', data={'file': file})

    assert_response_201(res, expected_data.encode())
    assert fn in os.listdir(UPLOAD_FOLDER)


def test_document_del():
    client = init()
    fn = UPLOAD_FOLDER + '/anotherfile.csv'
    with open(fn, 'w') as f:
        f.write('abc,def')

    res = client.delete(basepath + 'documents')
    assert_response(res)
    assert fn not in os.listdir(UPLOAD_FOLDER)


def test_document_style_post():
    client = init()
    data = generate_style()
    res = client.put(basepath + 'documents/1/style', json=data)
    assert res.status_code == 200


def test_document_style_post_invalid():
    client = init()
    data = generate_style()
    data['header']['margin']['left'] = 'null'
    res = client.put(basepath + 'documents/1/style', json=data)

    assert res.status_code == 400

    expected = b'footer.margin.left: could not convert string to float'
    assert expected in res.get_data()


def test_document_style_post_missing():
    client = init()
    data = generate_style()
    del data['header']
    res = client.put(basepath + 'documents/1/style', json=data)

    assert res.status_code == 400


def test_route_verify_server():
    client = init()

    host = 'www.python.org'
    response = client.post(basepath + f'server/verify?URL={host}')
    result = json.loads(response.data.decode())
    assert response.status_code == 200
    assert result['success']
    assert result['msg'] == ''

    host = 'www.never.python.org'
    response = client.post(basepath + f'server/verify?URL={host}')
    result = json.loads(response.data.decode())
    assert response.status_code == 200
    assert not result['success']


def test_users_get():
    client = init()
    response = client.get(basepath + 'users')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 1000 in data
    assert 1009 in data


def test_users_user_get():
    client = init()
    response = client.get(basepath + 'users/1002')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'name' in data
    assert 'email' in data
    assert '2' in data['name']
    assert data['email'].endswith('company.com')


def test_users_post():
    client = init()
    user = {'name': 'test', 'email': 'a@test.com'}
    response = client.post(basepath + 'users', json=user)
    assert response.status_code == 201

    id = json.loads(response.data)
    assert id == 1010

    response = client.get(basepath + 'users/1010')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == user['name']
    assert data['email'] == user['email']


def test_users_post_unhappy():
    client = init()
    user = {'name': 'test'}
    response = client.post(basepath + 'users', json=user)
    assert response.status_code == 400


def assert_response(response, expected_data=b'ok'):
    assert response.status_code == HTTPStatus.OK
    assert response.get_data() == expected_data


def assert_response_201(response, expected_data=b'ok'):
    assert response.status_code == HTTPStatus.CREATED
    assert response.get_data() == expected_data


def verify_response(response,
                    expected_status=HTTPStatus.OK,
                    expected_data=None) -> bool:

    if expected_data is None:
        return response.status_code == expected_status

    return response.status_code == expected_status and \
        response.get_data() == expected_data


def requests(url='', N=LARGE_N, client: FlaskClient = None, **kwds):
    if client is None:
        client = init()

    yield from (client.get(url, **kwds) for _ in range(N))


def generate_style():
    element = {'border': {'style': 'dotted',
                          'width': 1.5,
                          'color': 'green',
                          'rounded': 5
                          },
               'margin': {'bottom': 0,
                          'left': 0,
                          'right': 0,
                          'top': 0
                          }}
    return {'header': element,
            'body': [element, element],
            'footer': element}


def init():
    app = init_server()
    client = app.test_client()
    return client


if __name__ == '__main__':
    # pytest.main()
    test_route_sleep()
