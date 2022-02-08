from dataclasses import dataclass
from time import sleep
from typing import List
import functools
import sys
import copy
import logging
import multiprocessing as mp
import queue

import util
from util import debug


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
        """Add an item to a queue, process the next item in the queue and return the result.
        The buffer is a FIFO queue and items are processed in-order.
        """
        if item is not None:
            self.append(item)

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

    def clear(self):
        self.buffer = []

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

    def __str__(self):
        values = ' '.join([self.__class__.__name__,
                           f'[ {self.process_item.__name__} ]',
                           'at',
                           hex(id(self))
                           ])
        return f'<{values}>'

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
        self.buffer.extend(reversed(group_of_items))

    def extend(self, groups_of_items):
        for group in reversed(groups_of_items):
            self.append(group)


@dataclass
class Resource:
    processor: Processor
    in_queue: queue.Queue
    out_queue: queue.Queue

    def start(self, max_items=None):
        self.handled_items = 0
        print('R', self.in_queue, self.out_queue)
        sys.stdout.flush()
        while True:
            if max_items is not None and self.handled_items >= max_items:
                return

            item = self.in_queue.get(block=True)

            self.processor.append(item)
            self.process()

    def process(self):
        while self.processor.buffer:
            result = self.processor.process()
            self.put(result)

    def put(self, item):
        self.out_queue.put(item)
        self.handled_items += 1


class Pipeline(Processor):
    """A Processor that combines of multiple processing-stages.

    Note that len(Pipeline) returns the length of the buffer of the whole Pipeline and not the total length of all components.
    """

    def __init__(self, items=[], *, processors: List[Processor] = []):
        super().__init__(items)
        self.init_processors(processors)

    def init_processors(self, processors: List[Processor]):
        self.processors = []
        for p in processors:
            # make a shallow copy of each processor
            processor = copy.copy(p)
            processor.clear()
            self.processors.append(processor)

    def __sizeof__(self) -> int:
        return len(self.processors)

    def __repr__(self):
        return '[' + ' > '.join(p.__name__ for p in self.processors) + ']'


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
        self.manager = mp.Manager()
        # TODO verify that the  manager class is mandatory

        # Note that buffer of Pipeline itself doesn't support concurrent access.
        n_queues = len(self.processors) + 1

        # self.queues = [self.manager.Queue() for _ in range(n_queues)]

        self.queues = [mp.Queue() for _ in range(n_queues)]
        print('qs', self.queues)
        self.resources = []

        # TODO transform constant to arg
        # TODO vary n_processes per process type
        # TODO use autoscaling
        n_processes = 1

        for q, processor in enumerate(self.processors):
            for p in range(n_processes):
                resource = Resource(
                    processor, self.queues[q], self.queues[q+1])
                assert resource.processor == processor
                assert resource.in_queue == self.queues[q]
                assert resource.out_queue == self.queues[q+1]

                assert id(resource.in_queue) == id(self.queues[q])
                process = mp.Process(target=resource.start)
                self.resources.append(process)

        assert len(self.resources) == n_processes * len(self.processors)

    def start_resources(self):
        for resource in self.resources:
            resource.start()

    def process(self, item=None):
        """ Process an item and then yield the result
        """
        if item is None and not self.buffer:
            return next(self)

        return super().process(item)

    def process_item(self, item):
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
        in_queue.put(item)

        print('Q', in_queue.empty(), out_queue.empty())
        # sleep(5)
        # print('Q', in_queue.empty(), out_queue.empty())
        sys.stdout.flush()
        return next(self)

    @property
    def in_queue(self):
        return self.queues[0]

    @property
    def out_queue(self):
        return self.queues[-1]

    def __next__(self):
        return self.out_queue.get()

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        for resource in self.resources:
            resource.terminate()

        self.manager.__exit__(*args)


class Push(Pipeline):
    pass


def constant_(x): return 1
def identity_(x): return x
def duplicate_(x): return x + x


constant = Processor.from_function(constant_)
identity = Processor.from_function(identity_)
duplicate = Processor.from_function(duplicate_)
