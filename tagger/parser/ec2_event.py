import logging

import boto3

from util.aws import ASGWrapper, EC2Wrapper
from .base_event import AWSEventParser

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class EC2EventParser(AWSEventParser):
    def __init__(self, session, event, context):
        self.session = session
        self.event = event
        self.context = context

    def get_created_instance_ids(self):
        instance_ids = []
        for instance in self.event['detail']['responseElements']['instancesSet'].get('items', []):
            instance_ids.append(instance['instanceId'])
        return instance_ids

    def get_resource_ids(self, event_name):
        response = self.event['detail']['responseElements']
        if event_name == 'CreateImage':
            return [response['imageId']]
        elif event_name == 'RunInstances':
            return self.get_created_instance_ids()
        elif event_name == 'CreateSecurityGroup':
            return [response['groupId']]
        elif event_name == 'CreateVolume':
            return [response['volumeId']]
        else:
            return []

    def invoked_by_asg(self):
        try:
            return self.event['detail']['userIdentity']['invokedBy'] == 'autoscaling.amazonaws.com'
        except KeyError as e:
            logger.warning('Key doesnt exist: %s', str(e))
            return False

    def parse_event(self):
        event_name = self.get_event_name()
        resource_ids = self.get_resource_ids(event_name)
        if event_name == 'RunInstances' and self.invoked_by_asg():
            username = ASGWrapper(self.session).get_asg_user_tag_by_instance_id(
                self.get_created_instance_ids())
        else:
            username = self.get_username()
        return username, resource_ids

    