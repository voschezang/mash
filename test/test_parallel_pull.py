from contextlib import contextmanager
from dataclasses import dataclass
from dis import dis
from importlib.metadata import distribution
from socket import timeout
from time import sleep
from typing import Dict, List
import functools
import multiprocessing as mp
import pytest
import queue

import util


class Processor:
    """A queue-like object that can "process" items.

    The superclass `list` allows the "queue" to be sorted and grouped.
    * Use .append() or .extend() to add items to the queue/buffer
    * Use .process() to handle or process an item
    """

    def __init__(self, items=[]):
        self.buffer = list(items)
        if not items:
            assert self.buffer == []

        assert self.buffer == items

    def process(self, item=None):
        """ Process an item and then yield the result
        """
        if item is None:
            try:
                item = self.buffer.pop()
            except IndexError as e:
                raise IndexError(f'No item to process; {e}')

        return self.process_item(item)

    def process_item(self, item):
        """Override this method to change the default identiy method.
        """
        return item

    def ready_to_process(self) -> bool:
        return len(self.buffer) > 0

    @staticmethod
    def from_function(pure_func):
        """Decorator that defines a "stateless" processor

        Usage
        -----
        ```py
        new_func = Processor.from_function(func)
        ```
        Note that new_func and func must have the same name in order to be compatible with `pickle`.

        Parameters
        ----------
            pure_func : (object) -> object
        """
        p = Processor()
        p._set_process_item_func(pure_func)
        return p

    def _set_process_item_func(self, func):
        self.process_item = func
        # TODO rename function s.t. it can be pickled and used in mp.Process
        functools.update_wrapper(self, func)

    def append(self, *args):
        self.buffer.append(*args)

    def extend(self, *args):
        self.buffer.extend(*args)

    # def __sizeof__(self) -> int:
    #     """Return the buffer-size, i.e. the number of items in the queue that can be processed
    #     """
    #     return super().__sizeof__()

    def __call__(self, item=None):
        return self.process(item)

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        pass


class Buffer(Processor):
    """A Processor with an explicit buffer that can be used to adjust buffer sizes.
    E.g. group or split up items.
    """

    def __init__(self, *args, n=2, **kwds):
        super().__init__(*args, **kwds)
        self.n = n

    def full(self) -> bool:
        return len(self.buffer) >= self.n

    def __len__(self) -> int:
        return len(self.buffer)

    def __iter__(self):
        return iter(self.buffer)


class Combiner(Buffer):
    """ Many-to-one
    e.g. Combiner(n=2) transforms items into pairs of items
    """

    def process_item(self, item):
        if not self.ready_to_process():
            raise IndexError(f'Not enought item to process')

        selection = self.items[:self.n]
        self.items = self.items[self.n:]
        return selection

    def ready_to_process(self) -> bool:
        return len(self.buffer) > self.n


class Distributer(Buffer):
    """ One-to-many
    e.g. Distributer(n=2) transforms pairs into items
    """

    def append(self, group_of_items):
        self.buffer.extend(group_of_items)

    def extend(self, groups_of_items):
        self.buffer += groups_of_items
        for group in groups_of_items:
            self.append(group)


@dataclass
class Resource:
    processor: Processor
    in_queue: queue.Queue
    out_queue: queue.Queue

    def start(self, max_items=None):
        assert isinstance(self.processor, Processor)
        self.handled_items = 0
        while True:
            if max_items is not None and self.handled_items >= max_items:
                print('Resource done')
                return

            pre = self.in_queue.get()
            post = self.processor.process(pre)
            self.put(post)

    def put(self, item):
        print('Resource.put')
        self.out_queue.put(item)
        self.handled_items += 1


class Processors(list):
    def __repr__(self):
        return '[' + ' > '.join(p.__name__ for p in self.processors) + ']'


class Pipeline(Processor):
    """A Processor that combines of multiple processing-stages.

    Note that len(Pipeline) returns the length of the buffer of the whole Pipeline and not the total length of all components.
    """

    def __init__(self, items=[], *, processors: List[Processor] = []):
        super().__init__(items)
        self.processors = processors

    def __sizeof__(self) -> int:
        return len(self.processors)


class Pull(Pipeline):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        # self.manager: mp.Manager
        self.queues: List[mp.Queue]
        self.resources: List[List[mp.Process]]
        self.initial_batch_size = 1

        self.init_resources()
        self.start_resources()

    def init_resources(self):
        # self.manager = mp.Manager()
        # TODO verify that the  manager class is mandatory

        # Note that buffer of Pipeline itself doesn't support concurrent access.
        n_queues = len(self.processors) + 1
        self.queues = [mp.Queue() for _ in range(n_queues)]
        # self.queues = [self.manager.Queue() for _ in range(n_queues)]
        self.resources = []

        # TODO transform constant to arg
        # TODO vary n_processes per process type
        # TODO use autoscaling
        n_processes = 1

        for q, processor in enumerate(self.processors):
            self.resources = []
            assert processor != []

            for p in range(n_processes):
                print('init resource', q, q+1)
                resource = Resource(
                    processor, self.queues[q], self.queues[q+1])
                process = mp.Process(target=resource.start)
                self.resources.append(process)

    def start_resources(self):
        for resource in self.resources:
            resource.start()

    def process_item(self, item):
        print(len(self.queues))
        if len(self.queues) <= 1:
            return item

        in_queue = self.queues[0]
        out_queue = self.queues[-1]

        # batches = util.group(item, self.initial_batch_size)

        inventory_size = 2
        # for _ in range(inventory_size):
        #    if batches:
        #    for item in batches.pop():
        #        in_queue.put(batch)
        #    batch = out_queue.get()

        # for item in items:
        print('put')
        in_queue.put(item)

        # for i, item in enumerate(items):
        result = out_queue.get(timeout=3)
        print(0, item, result)
        return result

    def __enter__(self, *args):
        # self.manager.__enter__(*args)
        return self

    def __exit__(self, *args):
        # self.manager.__exit__(*args)
        for resource in self.resources:
            resource.terminate()


class Push(Pipeline):
    pass


# @Processor.from_function
def create_():
    return 1


# @Processor.from_function
def duplicate_(x):
    return x + x


# @Processor.from_function
def finalize_(batch):
    return batch


create = Processor.from_function(create_)
duplicate = Processor.from_function(duplicate_)
finalize = Processor.from_function(finalize_)


def test_Pipeline_1x1():
    value = 10
    processors = [duplicate]
    with Pull(processors=processors) as pipeline:
        assert len(pipeline.processors) == len(processors)

        for i, processor in enumerate(processors):
            assert pipeline.processors[i] == processor

        result = pipeline.append(value)
        assert len(pipeline.buffer) == 1
        assert pipeline.queues[0].empty()

        result = pipeline.process()
        assert result == 2 * value
        assert result != value

        for q in pipeline.queues:
            assert q.empty()


def test_Pipeline_1x1_with_empty_buffer():
    value = 11
    processors = [duplicate]
    with Pull(processors=processors) as pipeline:

        for _ in range(3):
            result = pipeline.process(value)

            assert result == 2 * value
            assert result != value

        for q in pipeline.queues:
            assert q.empty()


def test_Pipeline_with_multiple_items():
    return
    # init resources
    # stateless and stateful processors
    values = [10, 20]
    processors = [Distributer(), duplicate, finalize]
    with Pull(processors=processors) as pipeline:
        result = pipeline.process(values)

    assert result == values

    # assert len(results) == 10
    # assert sum(results) == vao


def test_Resource():
    in_queue = mp.Queue()
    out_queue = mp.Queue()

    # pre-fill queue
    in_queue.put(1)
    resource = Resource(Processor(), in_queue, out_queue)
    assert isinstance(resource.processor, Processor)
    resource.start(max_items=1)

    result = out_queue.get(timeout=1)
    assert result == 1


def test_Resource_mp():
    value = 'one'
    with mp.Manager() as manager:
        in_queue = manager.Queue()
        out_queue = manager.Queue()
        resource = Resource(Processor(), in_queue, out_queue)
        process = mp.Process(target=resource.start, args=(1,))

        # start before filling queue
        process.start()
        in_queue.put(value)

        # without timeout
        with pytest.raises(queue.Empty):
            out_queue.get(timeout=0)

        # timeout must be significant
        result = out_queue.get(timeout=.3)
        assert result == value

        with pytest.raises(queue.Empty):
            out_queue.get(timeout=.1)


def test_combiner():
    return
    combine = Combiner(n=2).process
    summer = Processor.from_function(sum)
    processors = [create, duplicate, combine, summer, combine, summer]

    with Pipeline(processors) as pipeline:
        results = list(pipeline.process(8))

    assert len(results) == 8 // 2 // 2
    assert sum(results) == 8


def test_Processor():
    # verify behaviour when empty
    items = [1]
    p = Processor()
    assert len(p.buffer) == 0
    with pytest.raises(IndexError):
        p.process()

    # verify behaviour when filled
    p.extend(items)
    assert len(p.buffer) == len(items)

    result = p.process()
    assert result == items[0]
    assert len(p.buffer) == 0


def test_Buffer():
    items = list(range(4))
    buffer = Buffer(items)
    assert len(Buffer(items)) == len(items)
    assert all(item in buffer for item in items)


def test_duplicate():
    assert duplicate.process
    assert duplicate.process_item
    assert isinstance(duplicate, Processor)

    value = 12
    assert duplicate(value) == 2 * value
    assert duplicate.process(value) == 2 * value

    process = mp.Process(target=duplicate, args=(value,))
    process.start()
    process.terminate()
    assert True


if __name__ == '__main__':
    pytest.main()
