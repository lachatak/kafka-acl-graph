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


def generate(acls, self_link_generator, generate_topic_download_link, get_static_resource, **kwargs):
    dot = Digraph(comment='Kafka Topic Graph')

    topic_nodes = set()
    username_nodes = set()
    edges = set()

    for acl in acls:
        topic_nodes.add(Node(acl['topic'],
                       {'shape': 'rectangle',
                        'label': f"<{topic_label(acl['topic'], self_link_generator, generate_topic_download_link, get_static_resource)}>"}))
        username_nodes.add(Node(acl['username'], {'shape': 'ellipse', 'style': 'filled', 'fillcolor': 'lawngreen',
                                         'label': acl['username'],
                                         'URL': self_link_generator(acl['username']),
                                         'tooltip': 'Zoom'}))
        if acl['permission'] == 'read':
            edges.add(Edge(acl['topic'], acl['username'], {'color': 'blue'}))
        elif acl['permission'] == 'write':
            edges.add(Edge(acl['username'], acl['topic'], {'color': 'red'}))
        else:
            edges.add(Edge(acl['topic'], acl['username'], {'color': 'blue'}))
            edges.add(Edge(acl['username'], acl['topic'], {'color': 'red'}))

    for node in username_nodes.union(topic_nodes):
        dot.node(node.name, **node.style)

    for edge in edges:
        dot.edge(edge.from_node, edge.to_node, **edge.style)

    print(dot.source)
    rendered = dot.render(uuid.uuid4().hex, directory='/tmp', format='svg', **kwargs)
    logger.info(f'File rendered to {rendered}')
    with open(rendered, "rb") as file:
        return rendered, file.read()


def topic_label(topic, self_link_generator, generate_topic_download_link, get_static_resource):
    return f"""
    <table border='0' cellborder='0' cellspacing='5'>
        <tr>
            <td href='{self_link_generator(topic)}' tooltip='Zoom'>{topic}</td>
        </tr>
        <tr>   
            <td href='{generate_topic_download_link(topic)}' tooltip='Get latest schema'>
                <table border='0' cellborder='0' cellspacing='0'>
                    <tr>
                        <td align='RIGHT'><img src='{get_static_resource('static/download.png')}'/></td>
                        <td align='LEFT'>Download</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """
