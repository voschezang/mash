from pytest import raises

from mash.functional_shell.ast.node import Node


def test_node():
    node = Node('abc')

    assert node.data == 'abc'

    with raises(NotImplementedError):
        node.run(None)
