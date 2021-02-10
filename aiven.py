import logging
import requests
import re
import cachetools.func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Aiven:
    def __init__(self, aiven_project, aiven_service, aiven_api_token):
        self.aiven_project = aiven_project
        self.aiven_service = aiven_service
        self.aiven_api_token = aiven_api_token

    def get_relevant_acls(self, include_pattern, exclude_user_pattern, exclude_topic_pattern):
        return [acl for acl in self.get_aiven_acls()
                if relevant(acl, include_pattern)
                and not irrelevant(acl, exclude_user_pattern, exclude_topic_pattern)]

    @cachetools.func.ttl_cache(maxsize=1, ttl=10 * 60)
    def get_aiven_acls(self):
        logger.info('Getting details from aiven')
        r = requests.get(f'https://api.aiven.io/v1/project/{self.aiven_project}/service/{self.aiven_service}/acl',
                         headers={
                             'Authorization': f'aivenv1 {self.aiven_api_token}'})
        return r.json()['acl']


def relevant(acl, include_pattern):
    if include_pattern == '':
        return True
    elif len(re.findall(include_pattern, acl['username'])) > 0 \
            or len(re.findall(include_pattern, acl['topic'])) > 0:
        return True
    else:
        return False


def irrelevant(acl, exclude_user_pattern, exclude_topic_pattern):
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
