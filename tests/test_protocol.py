import copy

import pytest

from shifthtml import protocol


class Node(protocol.Node):
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __replace__(self, /, **changes):
        return Node(self.value)

    def render(self, *args, **kwargs):
        yield f"Node({self.value}, children=["
        for child in self.children:
            yield from child.render(*args, **kwargs)
        yield "])"


class NodeTree(protocol.NodeTree):
    def render(self, *args, **kwargs):
        yield from self.root.render(*args, **kwargs)


def test_node_depth():
    node1 = Node("1")
    node2 = Node("2")
    node3 = Node("3")
    node1.add_child(node2)
    node2.add_child(node3)

    assert node1.children == [node2]
    assert node2.parent is node1
    assert node3.parent is node2
    assert node2.children == [node3]
    assert list(node1) == [node1, node2, node3]


def test_node_breadth():
    node1 = Node("1")
    node2_1 = Node("2.1")
    node2_2 = Node("2.2")
    node2_3 = Node("2.3")
    node3_1 = Node("3.1")
    node3_2 = Node("3.2")
    node3_3 = Node("3.3")
    node3_4 = Node("3.4")

    node1.add_child(node2_1)
    node1.add_child(node2_2)
    node1.add_child(node2_3)
    node2_2.add_child(node3_1)
    node2_2.add_child(node3_2)
    node2_3.add_child(node3_3)
    node2_3.add_child(node3_4)

    assert node1.children == [node2_1, node2_2, node2_3]
    assert node2_1.children == []
    assert node2_2.children == [node3_1, node3_2]
    assert node2_3.children == [node3_3, node3_4]
    assert node2_1.parent is node1
    assert node2_2.parent is node1
    assert node2_3.parent is node1
    assert node3_1.parent is node2_2
    assert node3_2.parent is node2_2
    assert node3_3.parent is node2_3
    assert node3_4.parent is node2_3

    assert [node.value for node in node1] == ["1", "2.1", "2.2", "3.1", "3.2", "2.3", "3.3", "3.4"]


def test_node_child_of_self():
    node1 = Node("1")
    with pytest.raises(ValueError, match="Can't make a node a child of itself"):
        node1.add_child(node1)


def test_node_add_unknown_type():
    with pytest.raises(ValueError, match="Node can only contain other nodes. Unexpected type 'str'"):
        Node("test").add_child("NotANode")


def test_nodetree_append_node():
    node1 = Node("1")
    node2 = Node("2")
    node3 = Node("3")
    node4 = Node("4")
    tree = NodeTree(node1, node1)

    tree2 = copy.deepcopy(tree)
    tree2.append(node2)
    tree3 = copy.deepcopy(tree2)
    tree3.append(node3)

    tree4 = copy.deepcopy(tree2)
    tree4.append(node4)

    assert tree is not tree2
    assert tree.root is node1
    assert tree.append_pointer is node1
    assert tree2.root.value == node1.value
    assert tree2.append_pointer.value == node2.value
    assert tree3.root.value == node1.value
    assert tree3.append_pointer.value == node3.value
    assert tree4.root.value == node1.value
    assert tree4.append_pointer.value == node4.value

    assert "".join(tree.render()) == "Node(1, children=[])"
    assert "".join(tree2.render()) == "Node(1, children=[Node(2, children=[])])"
    assert "".join(tree3.render()) == "Node(1, children=[Node(2, children=[Node(3, children=[])])])"
    assert "".join(tree4.render()) == "Node(1, children=[Node(2, children=[Node(4, children=[])])])"


def test_nodetree_append_nodetree():
    node1 = Node("1")
    node2 = Node("2")
    node3 = Node("3")
    node4 = Node("4")
    tree1 = NodeTree(node1, node1)
    tree1.append(node2)
    tree2 = NodeTree(node3, node3)
    tree2.append(node4)

    tree1.append(tree2)

    assert "".join(tree1.render()) == "Node(1, children=[Node(2, children=[Node(3, children=[Node(4, children=[])])])])"
