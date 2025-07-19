from pytest import raises

from mash.shell2.ast.node import Node


def test_node():
    node = Node()

    with raises(NotImplementedError):
        node.run(None)
