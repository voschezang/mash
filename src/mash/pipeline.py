from dataclasses import dataclass
from time import sleep
from typing import List, Tuple
from functools import update_wrapper
import copy
from enum import Enum, auto
import multiprocessing as mp
import queue


class Processor:
    """A queue-like object that can "process" items.

    The superclass `list` allows the "queue" to be sorted and grouped.
    * Use .append() or .extend() to add items to the queue/buffer.
    * Use .process() to handle or process an item.
    """

    def __init__(self, items=[]):
        self.buffer = list(items)

    def process(self, item=None):
        """Add an item to a queue, process the next item in the queue and return the result.
        Override this method to change queue behaviour into e.g. FIFO.
        """
        # if item is not None:
        #     self.append(item)

        if item is None and self.buffer:
            item = self.buffer.pop()
            # except IndexError as e:
            #     raise IndexError(f'No item to process; {e}')

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
        """Decorator that defines a "stateless" processor.

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
        update_wrapper(self, func)

    def append(self, *args):
        self.buffer.append(*args)

    def extend(self, *args):
        self.buffer.extend(*args)

    def __str__(self):
        values = [self.__class__.__name__,
                  f'[ {self.process_item.__name__} ]',
                  'at',
                  hex(id(self))]
        return f'<{" ".join(values)}>'

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
            raise IndexError('Not enought item to process')

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


class Strategy(Enum):
    push = auto()
    pull = auto()
    constant = auto()


@ dataclass
class Resource:
    processor: Processor
    delivery_queues: Tuple[queue.Queue, queue.Queue]
    demand_queues: Tuple[queue.Queue, queue.Queue] = None
    strategy: Strategy = Strategy.push

    def start(self, max_items=None):
        self.handled_items = 0

        while True:
            if max_items is not None and self.handled_items >= max_items:
                return

            self.wait_for_input_demand()
            self.demand_input()

            item = self.in_queue.get(block=True)

            self.processor.append(item)
            self.process()

    def wait_for_input_demand(self):
        if self.strategy == Strategy.push:
            # never wait
            return

        if self.strategy == Strategy.pull and self.demand_queues[1] is not None:
            self.demand_queues[1].get(block=True)

        # in case of Strategy.constant:
        # maintain a stable out_queue size
        while not self.out_queue.empty():
            sleep(0.01)
        return

    def demand_input(self):
        if self.strategy == Strategy.pull and self.demand_queues[0] is not None and self.demand_queues[0].empty():
            self.demand_queues[0].put(1)

    def process(self):
        while self.processor.buffer:
            result = self.processor.process()
            self.put(result)

    def put(self, item):
        self.out_queue.put(item)
        self.handled_items += 1

    @property
    def in_queue(self) -> queue.Queue:
        return self.delivery_queues[0]

    @property
    def out_queue(self) -> queue.Queue:
        return self.delivery_queues[1]


class Pipeline(Processor):
    """A Processor that combines of multiple processing-stages.

    Note that len(Pipeline) returns the length of the buffer of the whole Pipeline and not the total length of all components.
    """

    def __init__(self, items=[], *, processors: List[Processor] = []):
        super().__init__(items)

        self.processors: List[Processor]

        self.init_processors(processors)

    def init_processors(self, processors: List[Processor]):
        self.processors = []
        for p in processors:
            assert isinstance(p, Processor)
            # make a shallow copy of each processor
            processor = copy.copy(p)
            processor.clear()
            self.processors.append(processor)

    def __sizeof__(self) -> int:
        return len(self.processors)

    def __repr__(self):
        return '[' + ' > '.join(p.__name__ for p in self.processors) + ']'


class PushPull(Pipeline):
    n_processors = 1

    def __init__(self, *args, strategy=Strategy.constant, **kwds):
        """A Pipeline with queues to pass items to be processed to subsequent processors.
        """
        super().__init__(*args, **kwds)

        self.queues: List[mp.Queue]
        # self.delivery_queues: List[mp.Queue] = self.queues
        self.demand_queues: List[mp.Queue] = None
        self.resources: List[List[mp.Process]]

        self.init_resources(strategy)
        self.start_resources()
        self.process_buffer()

    def init_resources(self, strategy):
        n_queues = len(self.processors) + 1
        self.queues = [mp.Queue() for _ in range(n_queues)]

        if strategy == Strategy.pull:
            self.demand_queues = [None] + [mp.Queue()
                                           for _ in range(n_queues - 1)]
        else:
            self.demand_queues = [None] * n_queues

        self.resources = []

        for q, processor in enumerate(self.processors):
            for p in range(PushPull.n_processors):
                resource = Resource(processor,
                                    self.queues[q: q + 2],
                                    self.demand_queues[q: q + 2],
                                    strategy)
                process = mp.Process(target=resource.start)
                self.resources.append(process)

    def start_resources(self):
        for resource in self.resources:
            resource.start()

    def process(self, item=None):
        """ Process an item and then yield the result
        """
        if self.demand_queues[-1] is not None:
            # send a reverse signal to indicate demand
            self.demand_queues[-1].put(1)

        if item is None and not self.buffer:
            return next(self)

        return super().process(item)

    def process_item(self, item):
        if not self.processors:
            return item

        self.append(item)
        return next(self)

    def process_buffer(self):
        for item in self.buffer:
            self.append(item)

    def append(self, item):
        # forward item to self.in_queue instead of self.buffer
        self.in_queue.put(item)

    def extend(self, items):
        for item in items:
            self.append(item)

    @ property
    def in_queue(self):
        return self.queues[0]

    @ property
    def out_queue(self):
        return self.queues[-1]

    def __next__(self):
        return self.out_queue.get()

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        for resource in self.resources:
            resource.terminate()


def constant_(*args): return 1
def identity_(x): return x
def duplicate_(x): return x + x


constant = Processor.from_function(constant_)
identity = Processor.from_function(identity_)
duplicate = Processor.from_function(duplicate_)
