from pytest import raises

from mash.shell2.ast.node import Node


def test_node():
    node = Node('abc')

    assert node.data == 'abc'

    with raises(NotImplementedError):
        node.run(None)
