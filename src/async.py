"""Generic parallelization functions using asyncio.
"""
from aiohttp import ClientSession
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import asyncio
import collections
import multiprocessing
import numpy as np
import sys
import time

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
    print(results)
    results = list(results)

    t2 = time.perf_counter_ns()
    dt = (t2 - t1) * 10**-9

    return results, dt


def parallel(func, batches, n_threads=2, *args, **kwds):
    """Executes func(*) for every batch.
    It is assumed that all function invocations are independent.

    Parameters
    ----------
        func : async funcion(client: aiohttp.ClientSession, *) -> Result
        batches : iterable of iterables
    """
    def partial(batches):
        return asynchronous(func, batches, *args, **kwds)

    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        yield from executor.map(partial, batches)


def asynchronous(func, inputs, concurrency=4, *args, **kwds):
    """Executes func(task) for every task in tasks.

    Parameters
    ----------
        func : async funcion(client: aiohttp.ClientSession, *) -> Result
        tasks : iterable of (unique) input for each function invocation
        * : constants arguments and keywords to be passed to each function
    """
    # reference: https://docs.aiohttp.org/en/stable/client_reference.html
    # create new event loop for thread safety
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(_wrapper(func, inputs, concurrency, *args, **kwds))

async def _wrapper(func, inputs, concurrency=2, *args, **kwds):
    queue = asyncio.Queue()
    #tasks = []
    for input_per_function in inputs:
        queue.put_nowait(input_per_function)

    tasks = [asyncio.create_task(_worker(func, queue, *args, **kwds))
            for _ in range(concurrency)]

    await queue.join()
    for task in tasks:
        task.cancel()

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return concat(results)


async def _worker(func, queue: asyncio.Queue, *args, **kwds):
    results = []
    async with ClientSession() as session:
        while True:
            try:
                task = await queue.get()
                #result = asyncio.ensure_future(func(session, task, *args, **kwds))
                result = await func(session, task, *args, **kwds)
                results.append(result)
                queue.task_done()

            except asyncio.CancelledError as error:
                return results


def concat(args=[]):
    return sum(args, [])


def batch_sizes(major: int, minor: int):
    batch_size = major * minor
    n_batches = max(n // batch_size, 1)

    if batch_size > n:
        # decrease minor batch size to avoid memory limits
        major, minor = n, 1

    return n_batches, major, minor

if __name__ == '__main__':
    # warning, this can cause high load
    url = 'http://localhost:8888/'
    n = 10000

    major_batch_size = 4 # per thread
    minor_batch_size = 64 # per async Task

    n_batches, major_batch_size, minor_batch_size = batch_sizes(major_batch_size, minor_batch_size)
    n_major_batches = max(n_batches // minor_batch_size, 1)
    batch_size = major_batch_size * minor_batch_size

    n_threads = min(multiprocessing.cpu_count() * 2, n)
    print(f'N: {n_batches * batch_size}, n_batches: {n_batches},',
            f' batch_size: {major_batch_size} x {minor_batch_size} = {n_batches},',
            f'n_threads: {n_threads}')

    # try non-threaded execution
    tasks = range(2)
    results = asynchronous(some_custom_func, tasks, concurrency=4, url=url)
    print('async', results)

    # a batch is a sequence of tasks
    batches = [range(major_batch_size)] * n_major_batches

    results, dt = main(some_custom_func, batches, n_threads=n_threads, url=url)

    # statistics
    statusses, times = zip(*concat(results))
    status = collections.Counter(statusses)
    mean_time = np.mean(times)
    tps = batch_size * n_batches / dt

    print(f'Runtime: {dt:.6f} seconds', file=sys.stderr)
    print(f'status: {status}, mean runtime: {mean_time:0.4f} s, number of requests: {batch_size * n_batches}, TPS: {tps:.2f}')
