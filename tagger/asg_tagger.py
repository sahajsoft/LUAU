import boto3
from tagger.parser.asg_event import AutoScalingEventParser
from util.aws import ASGWrapper
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ASGTagger:
    def __init__(self, event, context):
        self.session = boto3.Session()
        self.asg = ASGWrapper(self.session)
        self.event = event
        self.context = context
        self.parser = AutoScalingEventParser(self.session, self.event, self.context)

    def start(self):
        username, asg_name = self.parser.parse_event()
        tag = {
            'ResourceId': asg_name,
            'Key': 'Creator',
            'Value': username,
            'PropagateAtLaunch': True
        }

        self.asg.create_or_update_tags(Tags=[tag])

def lambda_handler(event, context):
    return ASGTagger(event, context).start()