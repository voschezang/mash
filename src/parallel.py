"""Generic parallelization functions using asyncio.
"""
from aiohttp import ClientSession
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import aiohttp
import asyncio
import collections
import multiprocessing
import numpy as np
import sys
import threading
import time
import traceback

import util

################################################################################
### Use-cases
################################################################################

async def simple_custom_func(session: ClientSession, i: int, url=''):
    async with session.get(url) as response:
        return response.status


async def some_custom_func(session: ClientSession, i: int, url='', timeout=10):
    #raise Exception('break;')
    timeout = aiohttp.ClientTimeout(total=timeout)
    t1 = time.perf_counter_ns()
    async with session.get(url, timeout=timeout) as response:
        async with response:

            # block until completion
            response.status == 200

            t2 = time.perf_counter_ns()
            dt = (t2 - t1) * 10**-9
            return response.status, dt

################################################################################
### Library Functions
################################################################################

def run(func, items, batch_size, duration, n_threads=2, **kwds):
    """Executes func(i) N x M times.
    It is assumed that all function invocations are independent.

    Parameters
    ----------
        func : async funcion(client: aiohttp.ClientSession, *) -> Result
        batches : iterable of iterables
    """
    refresh_interval = 0.5 # sec
    refresh_age = 0

    def partial(inputs):
        return asynchronous(func, inputs, **kwds)


    batches = util.group(items, batch_size)

    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        try:
            # TODO use lazy eval of items instead of .map
            generator = executor.map(partial, batches, timeout=duration)

            status = collections.Counter()
            times = []

            t1 = time.perf_counter_ns()
            dt = 0
            # use try-except to gracefully handle thread shutdown
            try:
                for results, errors in generator:
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

                # clear realtime line
                print('\n')

                if times:
                    show_status(status, times, dt)

            except Exception as e:
                print(e)
                traceback.print_exc()
                return False

            return True

        except TimeoutError as e:
            print(e)
            pass

    return status, times



def show_status(status, times, start_time, **kwds):
    dt = (time.perf_counter_ns() - start_time) * 10**-9
    mu = np.mean(times)
    rel_std = np.std(times) / mu * 100
    N = len(times)
    tps = N / dt

    out = f'> N: {N}, \t{status}, \tE[t]: {mu:0.4f} s ± {rel_std:.2f} % \tTPS: {tps:.2f}'
    print(out, **kwds)


class Cancel(Exception):
    pass

def asynchronous(func, inputs, concurrency=4, **kwds):
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
    return loop.run_until_complete(_wrapper(func, inputs, concurrency, **kwds))


async def _wrapper(func, inputs, concurrency=2, **kwds):
    queue = asyncio.Queue()
    # TODO don't pre-emtively define work, but do it JIT, 
    #   then keep thread/job alive instead re-creating it,
    #   and then increase workload per thread
    for input_per_function in inputs:
        queue.put_nowait(input_per_function)

    tasks = [asyncio.create_task(worker(func, queue, **kwds))
            for _ in range(concurrency)]


    # wait for all input queue items to be completed
    await queue.join()

    # cancel any remaining tasks (e.g. when batch_size > n_threads)
    for task in tasks:
        task.cancel()

    # Note that the returned values of asyncio.gather may include instances of asyncio.CancelledError
    results_per_task = await asyncio.gather(*tasks, return_exceptions=True)
    results = []
    errors = []
    for item in results_per_task:
        try:
            r, e = item
            results.extend(r)
            errors.extend(e)
        except TypeError as e:
            errors.append([e])

    return results, errors


async def worker(func, queue: asyncio.Queue,
        results=[], errors=[], **kwds):
    try:
        async with ClientSession() as session:
            while True:
                # TODO use get_nowait, and return on asyncio.QueueEmpty to safe resources
                task = await queue.get()
                await try_task(func, task, session, results, errors, **kwds)
                queue.task_done()

    except asyncio.CancelledError as error:
        return results, errors


async def try_task(func, inputs, session, results, errors, **kwds):
    try:
        result = await func(session, inputs, **kwds)
        results.append(result)

    except Exception as e:
        # e.g. aiohttp.client_exceptions.ClientConnectorError, ConnectorError
        # note that this does not include asyncio.CancelledError and asyncio.CancelledError
        errors.append(e)


def main():
    # warning, this can cause high load
    url = 'http://localhost:8888/'
    max_n = 1000
    batch_size_per_thread = 16
    concurrency_per_thread = 4
    n_threads = multiprocessing.cpu_count() * 2
    duration = 10

    # try non-threaded execution
    results = asynchronous(some_custom_func, range(1), concurrency=2, url=url)
    print('async', results)

    run(some_custom_func, range(max_n), batch_size_per_thread, duration,
            n_threads=n_threads, concurrency=concurrency_per_thread, url=url)

if __name__ == '__main__':
    main()
    print('done')
