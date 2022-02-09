
from multiprocessing.sharedctypes import Value
import aiohttp
from aiohttp import ClientSession
import time

import util
from server import basepath
from parallel import asynchronous
from pipeline import Processor, Pull, Pipeline, identity, duplicate

url = 'http://localhost:5000' + basepath


async def get(session: ClientSession, i: int, url='', timeout=10, **kwds):
    timeout = aiohttp.ClientTimeout(total=timeout)
    async with session.get(url, timeout=timeout, **kwds) as response:
        async with response:
            result = await response.content.read()
            return response.status, result.decode()


async def post(session: ClientSession, i: int, url='', timeout=10, **kwds):
    timeout = aiohttp.ClientTimeout(total=timeout)
    async with session.post(url, timeout=timeout, **kwds) as response:
        async with response:
            result = await response.content.read()
            return response.status, result.decode()


def parse_response_(response, default=None) -> int:
    items, errors = response
    if errors:
        return default

    results = []
    for status, result in items:
        if status == 200:
            results.append(result)
        else:
            return default

    return results


def to_int_(s: str) -> int:
    return int(s)


parse_response = Processor.from_function(parse_response_)
to_int = Processor.from_function(to_int_)


def echo(json, n_calls=1):
    endpoint = 'echo'
    results, errors = asynchronous(post, range(n_calls),
                                   concurrency=1,
                                   url=url + endpoint,
                                   json=json)

    return results, errors


def echo_offline(json):
    return [(200, json)], []


def call_api(n_calls=1):
    endpoint = 'stable'
    endpoint = 'scrambled'
    endpoint = 'noisy'
    endpoint = 'echo'
    results, errors = asynchronous(get, range(n_calls),
                                   concurrency=1,
                                   url=url + endpoint)

    return results, errors


def test_compute_pipeline():
    items = [str(i) for i in range(10)]
    results = []

    # processors = [Processor.from_function(echo_offline)]
    processors = [Processor.from_function(echo)]
    with Pull(processors=processors) as pipeline:

        for item in items:
            r, errors = pipeline.process(item)
            _, result = r[0]
            assert result == item


def compute():
    items = [str(i) for i in range(10)]
    results = []

    compute = Processor.from_function(echo)
    concat = Processor.from_function(util.concat)
    processors = [identity, compute, parse_response, concat, to_int, duplicate]
    with Pull(processors=processors) as pipeline:

        pipeline.extend(items)

        for item in items:
            result = pipeline.process()
            assert result == 2 * int(item)
            results.append(result)

    return results


if __name__ == '__main__':
    test_compute_pipeline()
    results = compute()
    print(results)
