"""Generic parallelization functions using asyncio.
"""
from aiohttp import ClientSession
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager
import aiohttp
import asyncio
import collections
import multiprocessing
import numpy as np
import sys
import time

from mash import util

################################################################################
# Use-cases
################################################################################


async def simple_custom_func(session: ClientSession, i: int, url=''):
    async with session.get(url) as response:
        return response.status


async def some_custom_func(session: ClientSession, i: int, url='', timeout=10):
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
# Library Functions
################################################################################


def run(func, items, batch_size, duration, n_threads=2, **kwds):
    """Executes func(i) N x M times.
    It is assumed that all function invocations are independent.

    Parameters
    ----------
        func : async funcion(client: aiohttp.ClientSession, *) -> Result
        items : inputs per function call
        batch_size : number of function call results that are yielded
        duration : timeout of the process. This evaluated between batches and not during batches.
        n_threads : int
        concurrency : max. number of async connections per thread
        **kwds : arguments for `func`. func(**kwds) must be threadsafe
        batches : iterable of iterables
    """
    refresh_interval = 0.5  # sec
    refresh_age = 0

    def partial(inputs):
        return asynchronous(func, inputs, **kwds)

    batches = util.group(items, batch_size)
    status = collections.Counter()
    exceptions = collections.defaultdict(collections.Counter)
    times = []

    t1 = time.perf_counter_ns()
    dt = 0

    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        try:
            # TODO use lazy eval of items instead of .map
            generator = executor.map(partial, batches, timeout=duration)

            # use try-except to gracefully handle thread shutdown
            for results, errors in generator:

                for error in errors:
                    exceptions[type(error)].update([str(error)])

                if results:
                    new_statusses, new_times = zip(*results)
                    status.update(new_statusses)
                    times.extend(new_times)

                    t2 = time.perf_counter_ns()
                    dt = (t2 - t1) * 10**-9

                    # show statistics
                    if dt - refresh_age > refresh_interval and util.verbosity():
                        refresh_age = 0
                        show_status(status, times, dt, exceptions, end='\r')

        except TimeoutError as e:
            print('Timeout')

    for k, v in exceptions.items():
        print(f'\n{k}\t {v}')

    if times:
        show_status(status, times, dt, exceptions, new_line=True)

    return status, times, exceptions


def show_status(status, times, dt, exceptions=[], new_line=False, **kwds):
    # sort statusses for readability
    status = {k: v for k, v in sorted(status.items())}

    if new_line:
        print('\n' + '-' * util.terminal_size().columns)

    n_exceptions = len([v.values for v in exceptions.values()])

    mu = np.mean(times)
    rel_std = np.std(times) / mu * 100
    N = len(times)
    tps = N / dt
    total = N + n_exceptions

    out = f'> N: {N}/{total}, \t{status}, \tE[t]: {mu:0.4f} s ± {rel_std:.2f} % \tTPS: {tps:.2f}'
    print(out, **kwds)


def asynchronous(func, inputs, concurrency=4, **kwds):
    """Executes func(task) for every task in tasks.

    Parameters
    ----------
        func : async funcion(client: aiohttp.ClientSession, *) -> Result
        tasks : iterable of (unique) input for each function invocation
        * : constants arguments and keywords to be passed to each function
    """
    if concurrency < 1:
        raise ValueError()

    # reference: https://docs.aiohttp.org/en/stable/client_reference.html
    # create new event loop for thread safety
    with new_event_loop() as loop:
        result = loop.run_until_complete(
            _wrapper(func, inputs, concurrency, **kwds))

    return result


async def _wrapper(func, inputs, concurrency=2, **kwds):
    queue = asyncio.Queue()
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
        except TypeError:
            errors.append([item])

    return results, errors


# async def worker(func, queue: asyncio.Queue, results: list, errors: list, **kwds):
async def worker(func, queue: asyncio.Queue, results=[], errors=[], **kwds):
    # immediately start the try-block to allow cancellation
    try:
        # copy variables to prevent mutable state
        results = results.copy()
        errors = results.copy()

        async with ClientSession() as session:
            while True:
                # TODO use get_nowait, and return on asyncio.QueueEmpty to safe resources
                task = await queue.get()
                await try_task(func, task, session, results, errors, **kwds)
                queue.task_done()

    except asyncio.CancelledError as error:
        return results, errors
    except Exception as e:
        print('Warning, deadlock encounterd; queue.join() is waiting for .task_done()')
        sys.exit(8)


async def try_task(func, inputs, session, results, errors, **kwds):
    try:
        result = await func(session, inputs, **kwds)
        results.append(result)

    except Exception as e:
        # e.g. aiohttp.client_exceptions.ClientConnectorError, ConnectorError
        # note that this does not include asyncio.CancelledError and asyncio.CancelledError
        errors.append(e)


@contextmanager
def new_event_loop():
    # automatically close custom loop to prevent leaking resources
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


def main():
    # warning, this can cause high load
    url = 'http://localhost:5000/v1/noisy'
    duration = 1
    max_n = 1000
    batch_size_per_thread = 16
    concurrency_per_thread = 3
    n_threads = multiprocessing.cpu_count() * 2

    concurrency = concurrency_per_thread * n_threads
    #concurrency_per_thread = concurrency // max_n

    print(f'Duration: {duration} s, N: {max_n}, #connections: {concurrency}, #threads: {n_threads}',
          f'batch_size: {batch_size_per_thread}, concurrency_per_thread: {concurrency_per_thread}')

    # try non-threaded execution
    results = asynchronous(some_custom_func, range(1), concurrency=2, url=url)
    print('async', results)

    run(some_custom_func, range(max_n), batch_size_per_thread, duration,
        n_threads=n_threads, concurrency=concurrency_per_thread, url=url)


if __name__ == '__main__':
    main()
    print('done')
