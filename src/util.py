import os

def concat(items=[]):
    """Concatenate items
    """
    return sum(items, [])


def group(items, n):
    """Group items by chunks of size n.
    I.e. a lazy version of itertools.pairwise with variable groupsize.
    """
    buffer = []
    for item in items:
        buffer.append(item)
        if len(buffer) == n:
            yield buffer
            buffer = []

    yield buffer


def extend(q, items):
    """Fill queue with items, similar to list.extend

    Parameters
    ----------
        w : queue.Queue or asyncio.Queue
    """
    for item in items:
        # Note that put_nowait is compatible with threading.Queue and asyncio.Queue
        q.put_nowait(item)


def terminal_size(default=(80, 100)):
    try:
        return os.get_terminal_size()
    except OSError:
        return default
