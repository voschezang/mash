import pytest

from aiohttp import ClientSession
from mash.parallel import *


# class Test(pytest.testcase):
#    def test_parallel(self):
#        q = queue.Queue()
#        n = 8
#        items = range(n)
#        res = parallel(stub, items)
#        self.assertEqual(len(res), n)
#
#    def test_parallel_one_by_one(self):
#        q = queue.Queue()
#        n = 8
#        items = range(n)
#        res = parallel(stub, items, batch_size=1, n_threads=1)
#        self.assertEqual(len(res), n)
#
#    def test_asynchronous(self):
#        in_queue, out_queue, _ = queues()
#        in_queue.put('')
#        res = asynchronous(stub, in_queue, out_queue)
#        self.assertEqual(len(res), n)
#
# def asynchronous(func, in_queue, out_queue, kwds):
#
#    def test_worker(self):
#        q = queue.Queue()
#        worker(q, n=2)


class NoResult(Exception):
    pass


async def stub(session: ClientSession, i: int, url=''):
    raise NoResult()

# def queues():
#     in_queue = queue.Queue()
#     out_queue = queue.Queue()
#     agg_queue = queue.Queue()
#     return in_queue, out_queue, agg_queue
