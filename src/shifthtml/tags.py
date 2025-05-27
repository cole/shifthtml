from .node import ElementNode, VoidElementNode, NodeType


class TagDefinition[T]:
    tag: str
    node_class: T

    def __init__(self, tag: str, node_class: T):
        self.tag = tag
        self.node_class = node_class

    def __call__(self, *args, **kwds) -> T:
        return self.node_class(self.tag, kwds, args or None)

    def __rshift__(self, other: NodeType) -> T:
        instance = self()
        return instance >> other



h1 = TagDefinition[ElementNode]("h1", ElementNode)
button = TagDefinition[ElementNode]("button", ElementNode)
ul = TagDefinition[ElementNode]("ul", ElementNode)
li = TagDefinition[ElementNode]("li", ElementNode)
img = TagDefinition[VoidElementNode]("img", VoidElementNode)
