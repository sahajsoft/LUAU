import boto3
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AWSEventParser:
    def __init__(self, session, event, context):
        self.session = session
        self.event = event
        self.context = context

    def get_username(self):
        """Get username

        Gets the username of the account that created the instance(s) in question

        Returns:
            str: Username of the account
        """
        return self.event['detail']['userIdentity'].get('userName', 'None')
    
    def get_event_name(self):
        return self.event['detail'].get('eventName', 'None')