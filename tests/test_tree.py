import copy

import pytest

from shifthtml import div, tree
from shifthtml.element import Fragment


class SimpleNode(tree.TreeNode):
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __replace__(self, /, **changes):
        return SimpleNode(self.value)

    def render(self, *args, **kwargs):
        yield f"Node({self.value}, children=["
        for child in self.children:
            if isinstance(child, tree.TreeNode):
                yield from child.render(*args, **kwargs)
            else:
                yield str(child)
        yield "])"

    async def arender(self, *args, **kwargs):
        for chunk in self.render(*args, **kwargs):
            yield chunk


def test_node_depth():
    node1 = SimpleNode("1")
    node2 = SimpleNode("2")
    node3 = SimpleNode("3")
    node1.append_child(node2)
    node2.append_child(node3)

    assert node1.children == [node2]
    assert node2.parent_node is node1
    assert node3.parent_node is node2
    assert node2.children == [node3]
    assert list(node1) == [node2]


def test_node_breadth():
    node1 = SimpleNode("1")
    node2_1 = SimpleNode("2.1")
    node2_2 = SimpleNode("2.2")
    node2_3 = SimpleNode("2.3")
    node3_1 = SimpleNode("3.1")
    node3_2 = SimpleNode("3.2")
    node3_3 = SimpleNode("3.3")
    node3_4 = SimpleNode("3.4")

    node1.append_child(node2_1)
    node1.append_child(node2_2)
    node1.append_child(node2_3)
    node2_2.append_child(node3_1)
    node2_2.append_child(node3_2)
    node2_3.append_child(node3_3)
    node2_3.append_child(node3_4)

    assert node1.children == [node2_1, node2_2, node2_3]
    assert node2_1.children == []
    assert node2_2.children == [node3_1, node3_2]
    assert node2_3.children == [node3_3, node3_4]
    assert node2_1.parent_node is node1
    assert node2_2.parent_node is node1
    assert node2_3.parent_node is node1
    assert node3_1.parent_node is node2_2
    assert node3_2.parent_node is node2_2
    assert node3_3.parent_node is node2_3
    assert node3_4.parent_node is node2_3

    assert list(node1) == [node2_1, node2_2, node2_3]

    assert [n.value for n in node1.walk() if isinstance(n, SimpleNode)] == [
        "1",
        "2.1",
        "2.2",
        "3.1",
        "3.2",
        "2.3",
        "3.3",
        "3.4",
    ]


def test_node_child_of_self():
    node1 = SimpleNode("1")
    with pytest.raises(ValueError, match="Can't make a node a child of itself"):
        node1.append_child(node1)


def test_node_accepts_string_children():
    node = SimpleNode("parent")
    node.append_child("text child")
    assert node.children == ["text child"]


def test_node_add_unknown_type():
    with pytest.raises(ValueError, match="Expected a TreeNode, str, or Template"):
        SimpleNode("test").append_child(42)  # type: ignore[invalid-argument-type]


def test_fragment_append_node():
    node1 = SimpleNode("1")
    node2 = SimpleNode("2")
    node3 = SimpleNode("3")
    node4 = SimpleNode("4")
    tree = Fragment(node1, node1)

    tree2 = copy.deepcopy(tree)
    tree2.append(node2)
    tree3 = copy.deepcopy(tree2)
    tree3.append(node3)

    tree4 = copy.deepcopy(tree2)
    tree4.append(node4)

    assert tree is not tree2
    assert tree.root is node1
    assert tree.append_pointer is node1
    assert isinstance(tree2.root, SimpleNode) and tree2.root.value == node1.value
    assert isinstance(tree2.append_pointer, SimpleNode) and tree2.append_pointer.value == node2.value
    assert isinstance(tree3.root, SimpleNode) and tree3.root.value == node1.value
    assert isinstance(tree3.append_pointer, SimpleNode) and tree3.append_pointer.value == node3.value
    assert isinstance(tree4.root, SimpleNode) and tree4.root.value == node1.value
    assert isinstance(tree4.append_pointer, SimpleNode) and tree4.append_pointer.value == node4.value

    assert "".join(tree.render()) == "Node(1, children=[])"
    assert "".join(tree2.render()) == "Node(1, children=[Node(2, children=[])])"
    assert "".join(tree3.render()) == "Node(1, children=[Node(2, children=[Node(3, children=[])])])"
    assert "".join(tree4.render()) == "Node(1, children=[Node(2, children=[Node(4, children=[])])])"


def test_fragment_append_fragment():
    node1 = SimpleNode("1")
    node2 = SimpleNode("2")
    node3 = SimpleNode("3")
    node4 = SimpleNode("4")
    tree1 = Fragment(node1, node1)
    tree1.append(node2)
    tree2 = Fragment(node3, node3)
    tree2.append(node4)

    tree1.append(tree2)

    assert "".join(tree1.render()) == "Node(1, children=[Node(2, children=[Node(3, children=[Node(4, children=[])])])])"


def test_fragment_rshift_does_not_mutate_original():
    d = div()
    f = Fragment(d, d)
    original_html = "".join(f.render())
    f2 = f >> "text"
    assert "".join(f.render()) == original_html
    assert "text" in "".join(f2.render())
