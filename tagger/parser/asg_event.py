"""ASG Event Parser module

This module parses the AWS Event dictionary for ASG Events to return needed data.

Note:
    The module expects specific AWS Event Data, passed through the event parameter. It one event type, referring
    to the event logged by creating an AutoScaling Group:
        * CreateAutoScalingGroup

"""

import boto3
import logging
from .base_event import AWSEventParser


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class AutoScalingEventParser(AWSEventParser):
    """Class used to parse all AWS ASG Events

    Attributes:
        session (obj): boto3 object for AWS Session
        event (dict): event object passed by caller process
        context (dict): context object passed by caller process

    """

    def __init__(self, session, event, context):
        self.session = session
        self.event = event
        self.context = context

    def get_asg_name(self):
        """Gets the name of the AutoScaling Group

        Returns: 
            str: Name of the ASG
        """
        return self.event['detail']['requestParameters'].get('autoScalingGroupName', 'None')

    def parse_event(self):
        """Parse the ASG Event

        Returns:
            str: The user email (or username) associated with the created ASG
            str: The name of the AutoScaling Group 
        """
        return self.get_username(), self.get_asg_name()
