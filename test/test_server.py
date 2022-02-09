import flask
from flask.testing import FlaskClient
import pytest
import server
from server import basepath
from http import HTTPStatus

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
    client = init()
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


def assert_response(response, expected_data=b'ok'):
    assert response.status_code == HTTPStatus.OK
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


def init():
    app = server.init()
    client = app.test_client()
    return client


if __name__ == '__main__':
    # pytest.main()
    test_route_sleep()
