# -*- coding: utf-8 -*-
"""EC2 tagger module

This module is deployed as a Lambda function within an AWS Environment. This function is responsible for
tagging EC2 instances/resources at creation with the email associated with the account creating the instance/resource.

Example:
    The function expects specific AWS Event Data, passed through the event parameter. It supports four events, each
    referring to a supported resource:
        * RunInstances
        * CreateSecurityGroup
        * CreateVolume
        * CreateImage
"""


import boto3
import os
from tagger.parser.ec2_event import EC2EventParser
from util.aws import EC2Wrapper
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
 
class EC2Tagger:
    """Class used to tag EC2 Resources

    Attributes:
        region (str): AWS Region the Lambda resides in
        session (obj): boto3 object for AWS Session
        ec2 (obj): abstracts AWS EC2 calls via EC2Wrapper
        event (dict): event object passed by lambda_handler
        context (dict): context object passed by lambda_handler
        parser (obj): Class used to parse the event dictionary

    """
    def __init__(self, event, context):
        self.region = os.environ['AWS_REGION']
        self.session = boto3.Session(region_name=self.region)
        self.ec2 = EC2Wrapper(self.session)
        self.event = event
        self.context = context
        self.parser = EC2EventParser(self.session, self.event, self.context)

    def start(self):
        """Tagger entry point

        This method is called by the lambda handler. It parses the event and tags the appropriate resources.

        Returns:
            dict: Response from AWS API call to create tags on desired resources

        """
        username, resource_ids = self.parser.parse_event()
        username_tag = {
            'Key': 'Creator',
            'Value': username
        }
        return self.ec2.create_tags(
            Resources=resource_ids,
            Tags=[username_tag]
        )


def lambda_handler(event, context):
    """Lambda entry point
    
    This is the handler associated with this lambda function. It instantiates a new EC2Tagger and passes
    down the event data.

    Args:
        event (dict): Event dictionary passed by AWS
        context (dict): Context dictionary passed by AWS (not used but required by AWS)
    
    Returns:
        dict: response from the EC2Tagger.start()
    """
    return EC2Tagger(event, context).start()

