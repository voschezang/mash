import pytest
from queue import Empty
import multiprocessing as mp

from mash.pipeline import *


def test_Resource():
    in_queue = mp.Queue()
    out_queue = mp.Queue()

    # pre-fill queue
    in_queue.put(1)
    resource = Resource(Processor(), (in_queue, out_queue))
    assert isinstance(resource.processor, Processor)
    resource.start(max_items=1)

    result = out_queue.get(timeout=.3)
    assert result == 1


class disabled_tests:
    # TODO fix below testcases

    def test_Resource_mp():
        value = 'one'
        with mp.Manager() as manager:
            in_queue = manager.Queue()
            out_queue = manager.Queue()
            resource = Resource(Processor(), (in_queue, out_queue))
            process = mp.Process(target=resource.start, args=(100,))

            # start before filling queue
            process.start()
            in_queue.put(value)

            # without timeout
            with pytest.raises(Empty):
                out_queue.get(timeout=0)

            # timeout must be significant
            result = out_queue.get(timeout=.3)
            assert result == value

            with pytest.raises(Empty):
                out_queue.get(timeout=.1)

    def test_Resource_with_pull_strategy():
        # a chain or pipeline of resources
        value = 22
        n_resources = 5
        processes = []
        with mp.Manager() as manager:
            delivery_queues = []
            demand_queues = []
            for i in range(n_resources + 1):
                delivery_queues.append(manager.Queue())
                demand_queues.append(manager.Queue())

            in_queue = delivery_queues[0]
            out_queue = delivery_queues[-1]

            for i in range(n_resources):
                resource = Resource(
                    Processor(),
                    delivery_queues[i:i+2],
                    demand_queues[i:i+2],
                    strategy=Strategy.pull)
                process = mp.Process(target=resource.start)
                processes.append(process)

                # start before filling queue
                process.start()

            with pytest.raises(Empty):
                out_queue.get(timeout=.1)

            # add items
            in_queue.put(value)

            # simulate demand
            demand_queues[-1].put(1)

            # timeout must be significant
            result = out_queue.get(timeout=2.3)
            assert result == value

            with pytest.raises(Empty):
                out_queue.get(timeout=.1)

        for process in processes:
            process.terminate()

    def test_Resource_with_push_strategy():
        # a chain or pipeline of resources
        value = 22
        n_resources = 5
        processes = []
        with mp.Manager() as manager:
            queues = []
            for i in range(n_resources + 1):
                queues.append(manager.Queue())

            in_queue = queues[0]
            out_queue = queues[-1]

            for i in range(n_resources):
                resource = Resource(
                    Processor(), queues[i:i+2], strategy=Strategy.push)
                process = mp.Process(target=resource.start)
                processes.append(process)

                # start before filling queue
                process.start()

            with pytest.raises(Empty):
                out_queue.get(timeout=.1)

            # add items
            in_queue.put(value)

            # timeout must be significant
            result = out_queue.get(timeout=.3)
            assert result == value

            with pytest.raises(Empty):
                out_queue.get(timeout=.1)

        for process in processes:
            process.terminate()

    def test_Resource_with_constant_strategy():
        # a chain or pipeline of resources
        value = 22
        n_resources = 5
        processes = []
        with mp.Manager() as manager:
            queues = []
            for i in range(n_resources + 1):
                queues.append(manager.Queue())

            in_queue = queues[0]
            out_queue = queues[-1]

            for i in range(n_resources):
                resource = Resource(
                    Processor(), queues[i:i+2], strategy=Strategy.constant)
                process = mp.Process(target=resource.start)
                processes.append(process)

                # start before filling queue
                process.start()

            # add items
            in_queue.put(value)

            # timeout must be significant
            result = out_queue.get(timeout=.3)
            assert result == value

            with pytest.raises(queue.Empty):
                out_queue.get(timeout=.1)

        for process in processes:
            process.terminate()

    def test_combiner():
        # TODO combiner doesn't have a return value when aggregating
        return
        combine = Combiner(n=2).process
        summer = Processor.from_function(sum)
        processors = [constant, duplicate, combine, summer, combine, summer]
        processors = [constant, combine, summer]

        with Pipeline(processors) as pipeline:
            pipeline.append()
            results = list(pipeline.process(8))

        assert len(results) == 8 // 2 // 2
        assert sum(results) == 8

    def test_Processor():
        # verify behaviour when empty
        items = [1]
        p = Processor()
        assert len(p.buffer) == 0
        result = p.process()
        assert result is None

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

    def test_constant():
        assert constant() == 1
        for i in range(3):
            assert constant(i) == 1

    def test_Pipeline_serial():
        value = 10
        processors = [duplicate]
        with PushPull(processors=processors) as pipeline:
            assert len(pipeline.processors) == len(processors)

            result = pipeline.append(value)
            result = pipeline.process()

            assert result == 2 * value
            assert result != value

            for q in pipeline.queues:
                assert q.empty()

    def test_Pipeline_with_empty_queue():
        value = 5
        with PushPull(processors=[duplicate]) as pipeline:
            pipeline.queues[-1].put(value)
            result = pipeline.process()
            assert result == value

    def test_Pipeline_serial_with_empty_buffer():
        value = 11
        processors = [duplicate]
        with PushPull(processors=processors) as pipeline:

            for _ in range(3):
                result = pipeline.process(value)

                assert result == 2 * value
                assert result != value

            for q in pipeline.queues:
                assert q.empty()

    def test_Pipeline_serial_with_multiple_processors():
        processors = [constant, identity, duplicate, identity, duplicate]
        with PushPull(processors=processors) as pipeline:

            pipeline.append(123)
            result = pipeline.process()

            assert result == 4

            for q in pipeline.queues:
                assert q.empty()

    def test_Pipeline_serial_with_multiple_items():
        items = list(range(2))
        items = [1]
        processors = [duplicate, constant, duplicate, constant]
        processors = [duplicate, constant]
        with PushPull(processors=processors) as pipeline:

            pipeline.extend(items)
            results = []
            for i in range(len(items)):
                result = pipeline.process()
                results.append(result)

        for i, item in enumerate(items):
            assert results[i] == 1

    def test_Pipeline_serial_with_group_of_one_item():
        batch = [10]
        # processors = [Distributer(n=2), duplicate, constant]
        processors = [Distributer(n=1), duplicate]
        results = []
        with PushPull(processors=processors) as pipeline:

            pipeline.append(batch)
            for i in range(len(batch)):
                results.append(pipeline.process())

        assert len(results) == len(batch)

        for i, value in enumerate(batch):
            assert results[i] == 2 * value

    def test_Pipeline_serial_with_group_of_items():
        batch = [10, 20, 30]
        processors = [Distributer(n=3), duplicate]
        results = []
        with PushPull(processors=processors) as pipeline:

            pipeline.append(batch)
            for i in range(len(batch)):
                results.append(pipeline.process())

        assert len(results) == len(batch)

        for i in range(len(batch)):
            assert results[i] == 2 * batch[i]

    def test_Pipeline_serial_with_pull_strategy_simple():
        items = list(range(10))
        processors = [identity]
        with PushPull(processors=processors, strategy=Strategy.pull) as pipeline:

            with pytest.raises(Empty):
                pipeline.out_queue.get(timeout=0.1)

            pipeline.extend(items)

            sleep(0.1)
            assert pipeline.out_queue.empty()

            for i in items:
                result = pipeline.process()
                assert result == i

    def test_Pipeline_serial_with_pull_strategy():
        items = list(range(10))
        processors = [duplicate, identity, duplicate]
        with PushPull(processors=processors, strategy=Strategy.pull) as pipeline:

            pipeline.extend(items)

            for i in items:
                result = pipeline.process()
                assert result == i * 4


if __name__ == '__main__':
    pytest.main()
