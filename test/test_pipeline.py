import pytest

from pipeline import *


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
