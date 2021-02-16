import logging
from flask import Flask, request, Response, jsonify
from urllib.parse import unquote
import os
from aiven import Aiven
import graph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')

server_base_ulr = os.environ["SERVER_NAME"]
aiven = Aiven(os.environ["AIVEN_PROJECT"], os.environ["AIVEN_SERVICE"], os.environ["AIVEN_API_TOKEN"])
os.environ['GV_FILE_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static/')) + '/'


@app.route('/api/v1/graph.svg', methods=['GET'])
def kafka_acl_graph():
    include_pattern = unquote(request.args.get('include-pattern', ''))
    exclude_user_pattern = unquote(request.args.get('exclude-user-pattern', ''))
    exclude_topic_pattern = unquote(request.args.get('exclude-topic-pattern', ''))

    acls = aiven.get_aiven_acls()
    nodes, edges = graph.generate(acls, graph.SearchConditions(include_pattern, exclude_user_pattern, exclude_topic_pattern))
    rendered, content = graph.render(nodes, edges, graph.LinkGenerator(generate_self_link, generate_topic_download_link, get_static_resource))
    os.remove(rendered)
    logger.info(f'File {rendered} deleted')

    response = Response(response=content, status=200, mimetype="image/svg+xml")
    response.headers["Content-Type"] = "image/svg+xml; charset=utf-8"

    return response


@app.route('/api/v1/<string:topic>')
def send_static(topic):
    schema = aiven.get_latest_schema(topic)

    return jsonify(schema)


@app.route('/internal/swagger.yaml')
def swagger():
    return app.send_static_file('swagger.yaml')


@app.route('/internal/status')
def status():
    return 'OK'


def get_static_resource(resource):
    return f'{server_base_ulr}/{resource}'


def generate_topic_download_link(topic):
    return f'{server_base_ulr}/api/v1/{topic}'


def generate_self_link(pattern):
    return f'{server_base_ulr}/api/v1/graph.svg?include-pattern={pattern}'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

