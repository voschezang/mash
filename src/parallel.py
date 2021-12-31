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
import threading
import time
import traceback

################################################################################
### Use-cases
################################################################################

async def simple_custom_func(client: ClientSession, *args, url=''):
    async with client.get(url) as response:
        return response.status


async def some_custom_func(client: ClientSession, *args, url=''):
    timeout = aiohttp.ClientTimeout(total=10)
    t1 = time.perf_counter_ns()
    async with client.get(url, timeout=timeout) as response:
        async with response:

            # block until completion
            response.status == 200

            t2 = time.perf_counter_ns()
            dt = (t2 - t1) * 10**-9
            return response.status, dt

################################################################################
### Library Functions
################################################################################

def run(func, N, M, n_threads=2, *args, **kwds):
    refresh_interval = 0.2 # sec
    refresh_age = 0

    generator = parallel(some_custom_func, N, M,
            n_threads=n_threads, *args, **kwds)

    status = collections.Counter()
    times = []

    t1 = time.perf_counter_ns()
    dt = 0
    # use try-except to gracefully handle thread shutdown
    try:
        for results in generator:
            # update data
            if results:
                new_statusses, new_times = zip(*results)
                status.update(new_statusses)
                times.extend(new_times)

                t2 = time.perf_counter_ns()
                dt = (t2 - t1) * 10**-9

                # show statistics
                if dt - refresh_age > refresh_interval:
                    refresh_age = 0
                    show_status(status, times, dt, end='\r')

        if times:
            show_status(status, times, dt)

    except Exception as e:
        print(e)
        traceback.print_exc()
        return False

    return True


def show_status(status, times, start_time, **kwds):
    dt = (time.perf_counter_ns() - start_time) * 10**-9
    mu = np.mean(times)
    rel_std = np.std(times) / mu * 100
    N = len(times)
    tps = N / dt

    out = f'> N: {N}, \t{status}, \tE[t]: {mu:0.4f} s ± {rel_std:.2f} % \tTPS: {tps:.2f}'
    print(out, **kwds)


def parallel_with_time(func, N, M, n_threads=2, *args, **kwds):
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
    return loop.run_until_complete(_wrapper(func, inputs, concurrency, *args, loop=loop, **kwds))


async def _wrapper(func, inputs, concurrency=2, *args, loop=None, **kwds):
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
                await _do_task(func, queue, session, results, *args, **kwds)
                if 0:
                    task = await queue.get()

                    try:
                        result = await func(session, task, *args, **kwds)
                        results.append(result)


                    except Exception as e:
                        # e.g. aiohttp.client_exceptions.ClientConnectorError, ConnectorError
                        # note that this does not include asyncio.CancelledError and asyncio.CancelledError
                        print(f'{func}(..) failed:', type(e), e)

                    queue.task_done()

            except asyncio.CancelledError as error:
                return results


async def _do_task(func, queue: asyncio.Queue, session, results, *args, log_first_error=True, **kwds):
    task = await queue.get()

    try:
        result = await func(session, task, *args, **kwds)
        results.append(result)

    except Exception as e:
        # e.g. aiohttp.client_exceptions.ClientConnectorError, ConnectorError
        # note that this does not include asyncio.CancelledError and asyncio.CancelledError
        if log_first_error:
            print(f'{func}(..) failed:', type(e), e)
            #print(f'{func}(..) failed:', type(e), e, file=sys.stderr)
            log_first_error = False

    queue.task_done()


def concat(args=[]):
    return sum(args, [])


def batch_sizes(major: int, minor: int, N: int):
    batch_size = major * minor
    n_major_batches = max(N // batch_size, 1)

    if batch_size > N:
        # decrease minor batch size to avoid memory limits
        major, minor = N, 1

    return n_major_batches, major, minor


def main():
    # warning, this can cause high load
    url = 'http://localhost:8888/'
    n = 100
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

    run(some_custom_func, N=n_batches, M=batch_size,
            n_threads=n_threads, concurrency=async_concurrency, url=url)

if __name__ == '__main__':
    main()
    print('done')
