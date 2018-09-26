"""EC2 Event Parser module

This module parses the AWS Event dictionary for EC2 Events to return needed data.

Example:
    The module expects specific AWS Event Data, passed through the event parameter. It supports four events, each
    referring to a supported resource:
        * RunInstances
        * CreateSecurityGroup
        * CreateVolume
        * CreateImage

"""

import logging

import boto3

from util.aws import ASGWrapper, EC2Wrapper
from .base_event import AWSEventParser

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class EC2EventParser(AWSEventParser):
    """Class used to parse all AWS EC2 Events

    Attributes:
        session (obj): boto3 object for AWS Session
        event (dict): event object passed by caller process
        context (dict): context object passed by caller process

    """
    def __init__(self, session, event, context):
        self.session = session
        self.event = event
        self.context = context

    def get_created_instance_ids(self):
        """Gets the ids of created instances

        This is used for events from created EC2 Instances. 

        Returns:
            list: List of ids from the event

        """
        instance_ids = []
        for instance in self.event['detail']['responseElements']['instancesSet'].get('items', []):
            instance_ids.append(instance['instanceId'])
        return instance_ids

    def get_resource_ids(self, event_name):
        """Gets the ids of created resources

        This function merely returns a different part of the event depending upon
        the specific event type being processed.
        
        Returns:
            list: List of resource ids from the event

        """
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
        """Determines if the event was invoked by an ASG

        EC2 Instances started by an AutoScaling Group will not have the user data in the event,
        so we need to check if an instance was created by one in order to go get the user data from the ASG itself.

        Returns: 
            bool: True if created by ASG, False otherwise. 
        """
        try:
            return self.event['detail']['userIdentity']['invokedBy'] == 'autoscaling.amazonaws.com'
        except KeyError as e:
            logger.warning('Key doesnt exist: %s', str(e))
            return False

    def parse_event(self):
        """Parses the event dictionary

        Returns:
            str: The user email (or username) associated with the created resources
            list: ids of the created resources. 

        """
        event_name = self.get_event_name()
        resource_ids = self.get_resource_ids(event_name)

        # If the instance was created by an AutoScaling Group, we need to check the ASG tags for the user email
        if event_name == 'RunInstances' and self.invoked_by_asg():
            username = ASGWrapper(self.session).get_asg_user_tag_by_instance_id(
                self.get_created_instance_ids())
        else:
            username = self.get_username()
        return username, resource_ids

    