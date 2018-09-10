import boto3
import os
from tagger.parser.asg_event import AutoScalingEventParser
from util.aws import ASGWrapper
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ASGTagger:
    def __init__(self, event, context):
        self.region = os.environ['AWS_REGION']
        self.session = boto3.Session(region_name=self.region)
        self.asg = ASGWrapper(self.session)
        self.event = event
        self.context = context
        self.parser = AutoScalingEventParser(self.session, self.event, self.context)

    def start(self):
        username, asg_name = self.parser.parse_event()
        logger.info("%s created autoscaling group %s", username, asg_name)
        tag = {
            'ResourceId': asg_name,
            'Key': 'Creator',
            'ResourceType': 'auto-scaling-group',
            'Value': username,
            'PropagateAtLaunch': True
        }

        return self.asg.create_or_update_tags(Tags=[tag])
        

def lambda_handler(event, context):
    return ASGTagger(event, context).start()