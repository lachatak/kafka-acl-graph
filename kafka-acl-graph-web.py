from flask import Flask, request, Response
from urllib.parse import unquote
import os
from aiven import Aiven
import graph

app = Flask(__name__)

domain_name = os.environ["DOMAIN_NAME"]
aiven = Aiven(os.environ["AIVEN_PROJECT"], os.environ["AIVEN_SERVICE"], os.environ["AIVEN_API_TOKEN"])


@app.route('/api/v1/graph.svg', methods=['GET'])
def kafka_acl_graph():
    include_pattern = unquote(request.args.get('include-pattern', ''))
    exclude_user_pattern = unquote(request.args.get('exclude-user-pattern', ''))
    exclude_topic_pattern = unquote(request.args.get('exclude-topic-pattern', ''))

    acls = aiven.get_relevant_acls(include_pattern, exclude_user_pattern, exclude_topic_pattern)
    rendered, content = graph.generate(acls, generate_self_link)
    os.remove(rendered)

    response = Response(response=content, status=200, mimetype="image/svg+xml")
    response.headers["Content-Type"] = "image/svg+xml; charset=utf-8"

    return response


@app.route('/internal/status')
def status():
    return 'OK'


def generate_self_link(pattern):
    return f'https://{domain_name}/api/v1/graph.svg?include-pattern={pattern}'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

