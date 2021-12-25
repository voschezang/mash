"""Generic parallelization functions using asyncio.
"""
from aiohttp import ClientSession
from concurrent.futures import ThreadPoolExecutor
import collections
import aiohttp
import asyncio
import multiprocessing
import sys
import time
import numpy as np

################################################################################
### Use-cases
################################################################################

async def simple_custom_func(client: ClientSession, *args, url=''):
    async with client.get(url) as response:
        return response.status


async def some_custom_func(client: ClientSession, *args, url=''):
    t1 = time.perf_counter_ns()
    async with client.get(url) as response:
        async with response:

            response.status == 200

            t2 = time.perf_counter_ns()
            dt = (t2 - t1) * 10**-9
            return response.status, dt

################################################################################
### Library Functions
################################################################################

def main(func, batches, n_threads=2, *args, **kwds):
    """Extension of `parallel` with performance metrics
    """
    t1 = time.perf_counter_ns()

    results = parallel(func, batches, n_threads, *args, **kwds)
    results = list(results)

    t2 = time.perf_counter_ns()
    dt = (t2 - t1) * 10**-9

    return results, dt


def parallel(func, batches, n_threads=2, *args, **kwds):
    """Executes func(task) for every task in tasks.

    Parameters
    ----------
        func : async funcion(client: aiohttp.ClientSession, *) -> Result
        tasks : iterable
    """
    def partial(batches):
        return asynchronous(func, batches, *args, **kwds)


    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        #responses = [executor.submit(partial, batches[0])]
        yield from executor.map(partial, batches)


def asynchronous(func, tasks, *args, **kwds):
    """Executes func(task) for every task in tasks.

    Parameters
    ----------
        func : async funcion(client: aiohttp.ClientSession, *) -> Result
        tasks : iterable
    """
    # reference: https://docs.aiohttp.org/en/stable/client_reference.html
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(_wrapper(func, tasks, *args, **kwds))


async def _wrapper(func, tasks, *args, **kwds):
    results = []
    async with ClientSession() as session:
        for task in tasks:
            result = asyncio.ensure_future(func(session, task, *args, **kwds))
            results.append(result)

        return await asyncio.gather(*results)


if __name__ == '__main__':
    # warning, this can cause high load
    url = 'http://localhost:8888/'
    n = 1000
    batch_size = 64
    n_batches = min(n // batch_size, n)

    n_threads = min(multiprocessing.cpu_count() * 2, n)
    print('N', batch_size * n_batches, 'n_batches', n_batches, 'batch_size', batch_size, 'n_threads', n_threads)

    # try sequential execution
    tasks = range(2)
    results = asynchronous(some_custom_func, tasks, url=url)
    print('async', results)

    # a batch is a sequence of tasks
    batches = [range(batch_size)] * n_batches

    results, dt = main(some_custom_func, batches, url=url)

    # statistics
    statusses, times = zip(*sum(results, []))
    status = collections.Counter(statusses)
    mean_time = np.mean(times)
    tps = batch_size * n_batches / dt

    print(f'Runtime: {dt:.6f} seconds', file=sys.stderr)
    print(f'status: {status}, mean runtime: {mean_time:0.4f} s, number of requests: {batch_size * n_batches}, TPS: {tps:.2f}')
