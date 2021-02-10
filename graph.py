import logging
from graphviz import Digraph
from dataclasses import dataclass, field
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=True)
class Edge:
    from_node: str
    to_node: str
    style: dict = field(hash=False)


@dataclass(frozen=True, eq=True)
class Node:
    name: str
    style: dict = field(hash=False)


def generate(acls, self_link_generator, **kwargs):
    dot = Digraph(comment='Kafka Topic Graph')

    nodes = set()
    edges = set()

    for acl in acls:
        nodes.add(Node(acl['topic'], {'shape': 'rectangle', 'URL': self_link_generator(acl['topic'])}))
        nodes.add(Node(acl['username'], {'shape': 'ellipse', 'style': 'filled', 'fillcolor': 'green',
                                         'URL': self_link_generator(acl['username'])}))
        if acl['permission'] == 'read':
            edges.add(Edge(acl['topic'], acl['username'], {'color': 'blue'}))
        elif acl['permission'] == 'write':
            edges.add(Edge(acl['username'], acl['topic'], {'color': 'red'}))
        else:
            edges.add(Edge(acl['topic'], acl['username'], {'color': 'blue'}))
            edges.add(Edge(acl['username'], acl['topic'], {'color': 'red'}))

    for node in nodes:
        dot.node(node.name, **node.style)

    for edge in edges:
        dot.edge(edge.from_node, edge.to_node, **edge.style)

    rendered = dot.render(uuid.uuid4().hex, directory='/tmp', format='svg', **kwargs)
    logger.info(f'File rendered to {rendered}')
    with open(rendered, "rb") as file:
        return rendered, file.read()
