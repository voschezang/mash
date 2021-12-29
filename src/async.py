"""Generic parallelization functions using asyncio.
"""
from aiohttp import ClientSession
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import asyncio
import collections
import multiprocessing
import numpy as np
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

            # block until completion
            response.status == 200

            t2 = time.perf_counter_ns()
            dt = (t2 - t1) * 10**-9
            return response.status, dt

################################################################################
### Library Functions
################################################################################

def main(func, N, M, n_threads=2, *args, **kwds):
    """Extension of `parallel` with performance metrics
    """
    t1 = time.perf_counter_ns()

    results = parallel(func, N, M, *args, **kwds)
    # force evaluation
    results = list(results)

    t2 = time.perf_counter_ns()
    dt = (t2 - t1) * 10**-9

    return results, dt


def parallel(func, N, M, n_threads=2, *args, **kwds):
    """Executes func(i) N x M times.
    It is assumed that all function invocations are independent.

    Parameters
    ----------
        func : async funcion(client: aiohttp.ClientSession, *) -> Result
        batches : iterable of iterables
    """
    def partial(n):
        inputs = range(n * N, n * N + M)
        return asynchronous(func, inputs, *args, **kwds)

    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        yield from executor.map(partial, range(N))


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
                result = await func(session, task, *args, **kwds)
                results.append(result)
                queue.task_done()

            except Exception as e:
                # e.g. aiohttp.client_exceptions.ClientConnectorError, ConnectorError
                # note that this does not include asyncio.CancelledError and asyncio.CancelledError
                queue.task_done()
            except asyncio.CancelledError as error:
                return results


def concat(args=[]):
    return sum(args, [])


def batch_sizes(major: int, minor: int, N: int):
    batch_size = major * minor
    n_major_batches = max(N // batch_size, 1)

    if batch_size > N:
        # decrease minor batch size to avoid memory limits
        major, minor = N, 1

    return n_major_batches, major, minor

if __name__ == '__main__':
    # warning, this can cause high load
    url = 'http://localhost:8888/'
    n = 1000
    async_concurrency = 16
    n_threads = multiprocessing.cpu_count() * 2

    batch_size = 2 # per thread
    n_batches = max(n // batch_size, 1)
    n = n_batches * batch_size
    print(f'N: {n_batches} x {batch_size} = {n_batches * batch_size}',
            f'n_threads: {n_threads}, async concurrency: {async_concurrency}')


    # try non-threaded execution
    tasks = range(2)
    results = asynchronous(some_custom_func, tasks, concurrency=4, url=url)
    print('async', results)

    results, dt = main(some_custom_func, N=n_batches, M=batch_size,
            n_threads=n_threads, concurrency=async_concurrency, url=url)

    # statistics
    statusses, times = zip(*concat(results))
    status = collections.Counter(statusses)
    mu = np.mean(times)
    rel_std = np.std(times) / mu * 100
    mean_dt_per_thread = np.sum(times) / n_threads

    print(f'Runtime: {dt:.6f} seconds')

    tps = batch_size * n_batches / dt

    assert len(statusses) == batch_size * n_batches, (len(statusses), batch_size * n_batches)
    print(f'status: {status}, mean runtime: {mu:0.4f} s ± {rel_std:.2f} %, number of requests: {batch_size * n_batches}, TPS: {tps:.2f}')
