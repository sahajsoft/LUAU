import boto3
from .util.ec2_event_parser import EC2EventParser
from .util.aws import EC2Wrapper
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
 
class EC2Tagger:
    def __init__(self, event, context):
        self.session = boto3.Session()
        self.ec2 = EC2Wrapper(self.session)
        self.event = event
        self.context = context
        self.parser = EC2EventParser(self.session, self.event, self.context)

    def start(self):
        username, resource_ids = self.parser.parse_event()
        username_tag = {
            'Key': 'Creator',
            'Value': username
        }
        self.ec2.create_tags(
            Resources=resource_ids,
            Tags=[username_tag]
        )


def lambda_handler(event, context):
    return EC2Tagger(event, context).start()

