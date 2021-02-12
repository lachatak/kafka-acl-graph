import logging
from graphviz import Digraph
from dataclasses import dataclass, field
import uuid
from collections import Counter

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

    topics = set()
    username_nodes = set()
    topic_nodes = set()
    edges = set()

    for acl in acls:
        topics.add(acl['topic'])
        username_nodes.add(Node(acl['username'], {'shape': 'ellipse',
                                                  # 'style': 'filled',
                                                  # 'fillcolor': 'lawngreen',
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

    duplicated = get_duplicated_topics(topics)

    # add color to problematic topics
    for topic in topics:
        if is_problematic_topic(topic, duplicated):
            topic_nodes.add(Node(topic,
                           {'shape': 'rectangle',
                            'style': 'filled',
                            'fillcolor': 'yellow',
                            'label': f"<{topic_label(topic, self_link_generator, generate_topic_download_link, get_static_resource)}>"}))
        else:
            topic_nodes.add(Node(topic,
                           {'shape': 'rectangle',
                            'label': f"<{topic_label(topic, self_link_generator, generate_topic_download_link, get_static_resource)}>"}))

    for node in username_nodes.union(topic_nodes):
        dot.node(node.name, **node.style)

    for edge in edges:
        dot.edge(edge.from_node, edge.to_node, **edge.style)

    logger.debug(dot.source)
    rendered = dot.render(uuid.uuid4().hex, directory='/tmp', format='svg', **kwargs)
    logger.info(f'File rendered to {rendered}')
    with open(rendered, "rb") as file:
        return rendered, file.read()


def is_problematic_topic(topic, duplicated):
    if topic_without_version(topic) in duplicated:
        return True
    else:
        return False


def topic_without_version(topic):
    return topic.split('_v')[0]


def get_duplicated_topics(topics):
    topics_without_version = [topic_without_version(topic) for topic in topics]
    c = Counter(topics_without_version)
    return [e for e in c if c[e] > 1]


def topic_label(topic, self_link_generator, generate_topic_download_link, get_static_resource):
    return f"""
    <table border='0' cellborder='0' cellspacing='5'>
        <tr>
            <td href='{self_link_generator(topic)}' tooltip='Zoom' align='CENTER' COLSPAN='2'>{topic}</td>
        </tr>
        <tr>   
            <td href='{generate_topic_download_link(topic)}' tooltip='Get latest schema'>
                <table border='0' cellborder='0' cellspacing='0'>
                    <tr>
                        <td align='RIGHT'><img src='{get_static_resource('static/magnifiying-glass.png')}'/></td>
                        <td align='LEFT'>Schema</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """
