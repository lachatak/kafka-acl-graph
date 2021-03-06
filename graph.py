import logging
import re
import uuid
from collections import Counter, namedtuple
from dataclasses import dataclass, field
from enum import Enum
from typing import List

from fn import _
from functional import seq
from graphviz import Digraph


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SearchConditions = namedtuple('SearchConditions', ['include_pattern', 'exclude_user_pattern', 'exclude_topic_pattern'])
LinkGenerator = namedtuple('LinkGenerator', ['self_link_generator', 'generate_topic_download_link', 'get_static_resource'])


class EdgeMode(Enum):
    READ = 1
    WRITE = 2


class NodeType(Enum):
    TOPIC = 1
    USERNAME = 2


class IncludeType(Enum):
    ALL = 1
    USERNAME = 2
    TOPIC = 3
    NONE = 4


@dataclass(frozen=True, eq=True)
class Edge:
    from_node: str
    to_node: str
    mode: EdgeMode


@dataclass(frozen=True, eq=True)
class Node:
    name: str
    type: NodeType
    problems: List[str] = field(default_factory=list, hash=False)
    included_in_search: bool = field(default=False, hash=False)


def generate(acls, search_conditions):
    relevant_acls = seq(acls) \
        .map(lambda x: add_search_result(x, search_conditions.include_pattern)) \
        .filter(lambda x: x['include_type'] in (IncludeType.ALL, IncludeType.TOPIC, IncludeType.USERNAME)) \
        .filter(lambda x: not excluded(x, search_conditions.exclude_user_pattern, search_conditions.exclude_topic_pattern))

    username_nodes = set()
    topic_nodes = set()
    edges = set()

    for acl in relevant_acls:
        username_nodes.add(Node(acl['username'], NodeType.USERNAME, [], acl['include_type'] == IncludeType.USERNAME))
        topic_nodes.add(Node(acl['topic'], NodeType.TOPIC, [], acl['include_type'] == IncludeType.TOPIC))

        if acl['permission'] == 'read':
            edges.add(Edge(acl['topic'], acl['username'], EdgeMode.READ))
        elif acl['permission'] == 'write':
            edges.add(Edge(acl['username'], acl['topic'], EdgeMode.WRITE))
        else:
            edges.add(Edge(acl['topic'], acl['username'], EdgeMode.READ))
            edges.add(Edge(acl['username'], acl['topic'], EdgeMode.WRITE))

    return mark_problematic_users(username_nodes) + mark_problematic_topics(topic_nodes), edges


def add_search_result(acl, include_pattern):
    if include_pattern == '':
        acl['include_type'] = IncludeType.ALL
        return acl
    elif len(re.findall(include_pattern, acl['username'])) > 0:
        acl['include_type'] = IncludeType.USERNAME
        return acl
    elif len(re.findall(include_pattern, acl['topic'])) > 0:
        acl['include_type'] = IncludeType.TOPIC
        return acl
    else:
        acl['include_type'] = IncludeType.NONE
        return acl


def excluded(acl, exclude_user_pattern, exclude_topic_pattern):
    if not exclude_user_pattern and not exclude_topic_pattern:
        return False
    elif not exclude_user_pattern and exclude_topic_pattern \
            and len(re.findall(exclude_topic_pattern, acl['topic'])) > 0:
        return True
    elif not exclude_topic_pattern and exclude_user_pattern \
            and len(re.findall(exclude_user_pattern, acl['username'])) > 0:
        return True
    elif exclude_user_pattern and exclude_topic_pattern and \
            (len(re.findall(exclude_user_pattern, acl['username'])) > 0
             or len(re.findall(exclude_topic_pattern, acl['topic']))) > 0:
        return True
    else:
        return False


def mark_problematic_users(users):
    def mark_invalid(user):
        if '*' in user.name:
            user.problems.append('Invalid ACL service name! Add explicit service name without wildcards!')
            return user
        else:
            return user

    return [mark_invalid(user) for user in users]


def mark_problematic_topics(topics):
    duplicated_topics = get_duplicated_topics(map(_.name, topics))

    def mark_duplicated(topic):
        if topic_without_version(topic.name) in duplicated_topics:
            topic.problems.append('Topic with multiple version numbers! Remove old topic definition when it is not used!')
            return topic
        else:
            return topic

    return [mark_duplicated(topic) for topic in topics]


def topic_without_version(topic):
    return topic.split('_v')[0]


def get_duplicated_topics(topics):
    topics_without_version = [topic_without_version(topic) for topic in topics]
    c = Counter(topics_without_version)
    return [e for e in c if c[e] > 1]


def render(nodes, edges, link_generator):
    dot = Digraph(comment='Kafka Topic Graph')

    for edge in edges:
        if edge.mode == EdgeMode.READ:
            attrs = {'color': 'blue'}
            dot.edge(edge.from_node, edge.to_node, **attrs)
        else:
            attrs = {'color': 'red'}
            dot.edge(edge.from_node, edge.to_node, **attrs)

    for node in nodes:
        if node.type == NodeType.USERNAME:
            add_username_node(dot, node, link_generator)
        else:
            add_topic_node(dot, node, link_generator)

    # logger.info(dot.source)
    rendered = dot.render(uuid.uuid4().hex, directory='/tmp', format='svg')
    logger.info(f'File rendered to {rendered}')
    with open(rendered, "rb") as file:
        return rendered, file.read()


def add_username_node(dot, user, link_generator):
    style = {'shape': 'ellipse',
             'label': f"<{user_label(user, link_generator)}>"}

    style.update({'style': 'filled', 'fillcolor': 'lawngreen'}) if user.included_in_search else style
    style.update({'style': 'filled', 'fillcolor': 'yellow'}) if len(user.problems) > 0 else style

    dot.node(user.name, **style)


def add_topic_node(dot, topic, link_generator):
    style = {'shape': 'rectangle',
             'label': f"<{topic_label(topic, link_generator)}>"}

    style.update({'style': 'filled', 'fillcolor': 'lawngreen'}) if topic.included_in_search else style
    style.update({'style': 'filled', 'fillcolor': 'yellow'}) if len(topic.problems) > 0 else style

    dot.node(topic.name, **style)


def user_label(user, link_generator):
    return f"""
    <table border='0' cellborder='0' cellspacing='5'>
        <tr>
            <td href='{link_generator.self_link_generator(user.name)}' tooltip='Zoom' align='CENTER' COLSPAN='2'>{user.name}</td>
        </tr>
        <tr> 
            {contact(user, link_generator)}
            {warning(user, link_generator)}
        </tr>
    </table>
    """


def topic_label(topic, link_generator):
    return f"""
    <table border='0' cellborder='0' cellspacing='5'>
        <tr>
            <td href='{link_generator.self_link_generator(topic.name)}' tooltip='Zoom' align='CENTER' COLSPAN='3'>{topic.name}</td>
        </tr>
        <tr>   
            <td href='{link_generator.generate_topic_download_link(topic.name)}' tooltip='Get latest schema' align='CENTER'>
                <table border='0' cellborder='0' cellspacing='0'>
                    <tr>
                        <td align='RIGHT'><img src='{link_generator.get_static_resource('static/menu.png')}'/></td>
                        <td align='LEFT'>Schema</td>
                    </tr>
                </table>
            </td>
            {contact(topic, link_generator)}
            {warning(topic, link_generator)}
        </tr>
    </table>
    """


def warning(node, link_generator):
    return f"""
            <td href='#' tooltip='{' '.join(map(str, node.problems))}' align='CENTER'>
               <table border='0' cellborder='0' cellspacing='0'>
                    <tr>
                        <td align='RIGHT'><img src='{link_generator.get_static_resource('static/warning.png')}'/></td>
                        <td align='LEFT'>Warning</td>
                    </tr>
                </table>
            </td>
            """ if len(node.problems) > 0 else "<td></td>"


def contact(node, link_generator):
    return f"""
            <td href='#' tooltip='Contact with owner' align='CENTER'>
                <table border='0' cellborder='0' cellspacing='0'>
                    <tr>
                        <td align='RIGHT'><img src='{link_generator.get_static_resource('static/email.png')}'/></td>
                        <td align='LEFT'>Contact</td>
                    </tr>
                </table>
            </td>
            """
