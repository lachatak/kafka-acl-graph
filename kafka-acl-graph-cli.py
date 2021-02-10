import click
import os
from aiven import Aiven
import graph


@click.command()
@click.option('--include-pattern', '-ip', default='', help='Include user or topic based on the provided regex pattern')
@click.option('--exclude-user-pattern', '-eup', default="", help='Exclude user pattern')
@click.option('--exclude-topic-pattern', '-etp', default="", help='Exclude topic pattern')
@click.option('--aiven-project', '-p', required=True, help='Aiven project')
@click.option('--aiven-service', '-s', required=True, help='Aiven service')
@click.option('--aiven-api-token', '-t', required=True, help='Aiven API token')
def main(include_pattern, exclude_user_pattern, exclude_topic_pattern, aiven_project, aiven_service, aiven_api_token):
    """CLI tool to generate svg graph from Aiven acl config"""

    aiven = Aiven(aiven_project, aiven_service, aiven_api_token)
    acls = aiven.get_relevant_acls(include_pattern, exclude_user_pattern, exclude_topic_pattern)
    rendered, content = graph.generate(acls, lambda x: x, {'view': True})
    os.remove(rendered)


if __name__ == "__main__":
    main()
