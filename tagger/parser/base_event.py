"""Base AWS Event Parser module

This module abstracts common attributes from all AWS Events to reduce duplicate code. 
This module is not called directly and is used mainly as an inheritance for more specific event parsers. 

"""

import boto3
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AWSEventParser:
    """Class used as a base for all AWS Event parsing

    Attributes:
        session (obj): boto3 object for AWS Session
        event (dict): event object passed by caller process
        context (dict): context object passed by caller process

    """
    def __init__(self, session, event, context):
        self.session = session
        self.event = event
        self.context = context

    def get_username(self):
        """Get username

        Gets the username of the account that created the AWS Resource in question

        Returns:
            str: Username of the account
        """
        return self.event['detail']['userIdentity'].get('userName', 'None')
    
    def get_event_name(self):
        """Get event name

        Gets the AWS event name from the event dictionary.

        Returns:
            str: name of the event in question
        """
        return self.event['detail'].get('eventName', 'None')