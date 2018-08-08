import boto3
import logging
from .event_parser import AWSEventParser


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AutoScalingEventParser(AWSEventParser):
    def __init__(self, session, event, context):
        self.session = session
        self.event = event
        self.context = context
    
    def get_asg_name(self): 
        return self.event['detail']['requestParameters'].get('autoScalingGroupName', 'None')

    def parse_event(self):
        return self.get_username(), self.get_asg_name()
        
