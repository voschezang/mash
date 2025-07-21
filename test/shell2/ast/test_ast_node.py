from pytest import raises

from mash.shell2.ast.node import Node


class Dummy(Node):
    pass


def test_node():
    with raises(TypeError):
        node = Node()


def test_node_methods():
    Node.__abstractmethods__ = {}

    node = Node()

    assert node.run(None) is None
    assert str(node)
    assert node != ''
