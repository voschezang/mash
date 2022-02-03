"""Generic parallelization functions using asyncio.
"""
from aiohttp import ClientSession
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import aiohttp
import asyncio
import collections
import contextlib
from enum import Enum, auto
import functools
import multiprocessing
import numpy as np
import queue
import sys
import threading
import time
import traceback
import multiprocessing as mp

import util

################################################################################
### Use-cases
################################################################################

async def simple_custom_func(session: ClientSession, i:int, url=''):
    async with session.get(url) as response:
        return response.status

async def some_custom_func(session: ClientSession, i:int, url=''):
    raise Exception('break;')
    timeout = aiohttp.ClientTimeout(total=10)
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

def run(func, items, batch_size, n_threads=2, **kwds):
    refresh_interval = 0.2 # sec
    refresh_age = 0

    generator = parallel(some_custom_func, items, batch_size,
            n_threads=n_threads,  **kwds)

    status = collections.Counter()
    times = []

    t1 = time.perf_counter_ns()
    dt = 0
    # use try-except to gracefully handle thread shutdown
    try:
        for results, errros in generator:
            results = concat(results)
            errros = concat(errros)
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


def main_(func, *args, **kwds):
    events = queue.Queue()
    events = mp.Pipe()
    pool = inner(func)
    event = events.get()
    print(event)
    if event == 'timeout':
        pool.shutdown()
    elif event == 'done':
        'ok'


def main3():
    with LongLivingThreadsExecutor(max_workers=n_threads, timeout=timeout) as results:
        for results in results:
            handle(result)
            show_result(result)

class Event(Enum):
    DONE = auto()

def parallel(func, items, batch_size=1, n_threads=4, **kwds):
    """Execute a function in parallel threads alive
    Similar to concurrent.futures.ThreadPoolExecutor

    Parameters
    ----------
        func : async funcion(client: aiohttp.ClientSession, *) -> Result
        items : inputs per function call
        batch_size : number of function call results that are yielded
        n_threads : int
        queue_timeout : float
        concurrency : max. number of async connections
        **kwds : arguments for `func`. func(**kwds) must be threadsafe
    """
    results = []
    manager = mp.Manager()

    # keep threads running and continuously feed them work through queues
    #in_queue = queue.Queue()
    #out_queue = queue.Queue()
    #in_queue = mp.Queue()
    #out_queue = mp.Queue()
    #agg_queue = mp.Queue()

    events = queue.Queue()
    events = mp.Pipe(duplex=False)

    total_timeout = 5
    total_timeout = 10
    out_queue_timeout = 1

    n = len(items)

    def partial(i):
        return asynchronous(func, in_queue, out_queue, **kwds)

    #print('args', args)

    #with ThreadPoolExecutor(max_workers=n_threads) as executor:
    #pool = mp.Pool(processes=n_threads)

    with mp.Manager() as manager:
        in_queue = manager.Queue()
        out_queue = manager.Queue()
        agg_queue = manager.Queue()

        # allow threads to ask for work
        # event_queue = manager.Queue()

        args = [(func, in_queue, out_queue, kwds.copy()) for _ in range(n_threads)]

        with mp.Pool(processes=n_threads) as pool:

            results = pool.starmap_async(asynchronous, args, chunksize=batch_size)
            #print('p', pool, results)

            aggregator = mp.Process(target=handle_results, args=(n, in_queue, out_queue, agg_queue, events[1]))
            aggregator.start()
            # aggregate results in a new thread
            #threading.Thread(target=handle_results, args=[out_queue, events]).start()

            print('main ==>')
            if events[0].poll(timeout=total_timeout):
                event = events[0].recv()
                print('event', event)
            else:
                print('Timeout')

        for resource in [pool, aggregator]:
            resource.terminate()

    print('.... return')
    return results


def handle_results(max_n, in_queue,out_queue, agg_queue, sender):
    print('handle_results init')
    for n in range(max_n):
        #while True:
        print('handle_results put', n)
        in_queue.put(n)
        print('handle_results get', n)
        result = out_queue.get()
        #agg_queue.put(result)
        if result is None:
            break

        print('next', result)
    else:
        sender.send('done')


def Temp():
    try:
        # setup a constant number of long-running resources,
        # then pull work from a queue
        # let threads continuously pull for work
        # setup resources, but then let threads ask for tasks continuously
        workers = create_threads(n_threads, start=True, target=partial)
        yield workers
    finally:
        cleanup_resources(workers)


def lazy_map(func, args):
    # TODO
    pass


def free(threads):
    for t in threads:
        t.join(timeout=0)


def create_threads(n, *thread_args, start=False, **kwds):
    threads = (threading.Thread(*thread_args, **kwds) for _ in range(n))
    if start:
        for t in threads:
            t.start()

    return threads


def asynchronous(func, in_queue, out_queue, kwds):
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
    print('run loop')
    return loop.run_until_complete(_wrapper(func, in_queue, out_queue, **kwds))


async def _wrapper(func, in_queue, out_queue, queue_timeout, concurrency=2, **kwds):
    #while True:
    #    tasks = []
    #    for input_per_function in in_queue.get():
    #        tasks.append(

    #    tasks = (asyncio.create_task(
    #        _worker(func, local_in_queue, local_out_queue, **kwds))
    #            for _ in range(concurrency))


    # cache inputs and outputs
    local_in_queue = asyncio.Queue()
    local_out_queue = asyncio.Queue()

    # init tasks while local_in_queue is still empty


    while True:
        print('worker; wait for in_queue.get()', in_queue.qsize(), queue_timeout)

        for i in range(2):
            print('i', i, in_queue.qsize(), in_queue.empty())
            time.sleep(0.1)
            #batch = in_queue.get_nowait()
            #try:
            #    #batch = in_queue.get(block=False, timeout=.1)
            #    batch = in_queue.get_nowait()
            #    break
            #except queue.Empty():
            #    print('err', i)
            #    pass

        batch = in_queue.get(block=True, timeout=queue_timeout)
        #batch = in_queue.get_nowait()
        print('batch', batch, len(batch))
        stop

        #if batch is None:
        #    # abort
        #    print('done', batch)
        #    for worker in workers:
        #        worker.cancel()
        #    return

        batch_size = len(batch)

        print('worker; put in')
        for input_per_function in batch:
            print('i', input_per_function)
            local_in_queue.put_nowait(input_per_function)

        workers = (asyncio.create_task(
            worker(func, local_in_queue, local_out_queue, **kwds))
                for _ in range(concurrency))

        # wait for all input queue items to be completed
        await queue.join()

        # cancel any remaining tasks (e.g. when batch_size > n_threads)
        for task in tasks:
            task.cancel()

        # aggregate results
        batch = await asyncio.gather(*tasks, return_exceptions=True)

        #batch = []
        #print('worker; wait for out')
        #for _ in range(batch_size):
        #    out = await local_out_queue.get()
        #    batch.append(out)

        out_queue.put(batch)
        in_queue.task_done()



async def worker(func, in_queue: asyncio.Queue, out_queue: asyncio.Queue, **kwds):
    print('worker')
    results = []
    async with ClientSession() as session:
        while True:
            try:
                print('> session; await in_queue.')
                inputs = await in_queue.get()
                print('> session; try')
                result = await try_task(func, inputs, session, results, errors=[], **kwds)
                result.append(results)
                in_queue.task_done()

                #print('> session; put')
                #await out_queue.put(result)

            except asyncio.CancelledError as error:
                return results


async def try_task(func, inputs, session, results, errors, log_first_error=True, **kwds):
    try:
        result = await func(session, inputs, **kwds)
        return result, None

    except Exception as e:
        # e.g. aiohttp.client_exceptions.ClientConnectorError, ConnectorError
        # note that this does not include asyncio.CancelledError and asyncio.CancelledError
        return None, result


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
    async_concurrency = 2
    n_threads = multiprocessing.cpu_count() * 2
    n_threads = 2

    batch_size = 2 # per thread
    n_batches = max(n // batch_size, 1)
    n = n_batches * batch_size
    print(f'N: {n_batches} x {batch_size} = {n_batches * batch_size}',
            f'n_threads: {n_threads}, async concurrency: {async_concurrency}')


    # try non-threaded execution
    #tasks = range(2)
    #results = asynchronous(some_custom_func, tasks, concurrency=4, url=url)
    #print('async', results)

    #run(some_custom_func, N=n_batches, M=batch_size, n_threads=n_threads, concurrency=async_concurrency, url=url)
    parallel(some_custom_func, range(n), batch_size, 
            n_threads=n_threads, concurrency=async_concurrency, queue_timeout=5,
            url=url)

if __name__ == '__main__':
    main()
    print('done')
