# -*- coding: utf-8 -*-
"""ASG tagger module

This module is deployed as a Lambda function within an AWS Environment. This function is responsible for
tagging AutoScaling Groups at creation with the email associated with the account creating the group. It
also tags the group's instances and ensures future instances will inherit the tags. 

Note:
    The function expects specific AWS Event Data, passed through the event parameter. It supports one event referring
    to the creation of an AutoScaling Group:
        * CreateAutoScalingGroup
"""

import boto3
import os
from tagger.parser.asg_event import AutoScalingEventParser
from util.aws import ASGWrapper
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ASGTagger:
    """Class used to tag AutoScaling Groups and it's instances

    Attributes:
        region (str): AWS Region the Lambda resides in
        session (obj): boto3 object for AWS Session
        ec2 (obj): abstracts AWS ASG calls via ASGWrapper
        event (dict): event object passed by lambda_handler
        context (dict): context object passed by lambda_handler
        parser (obj): Class used to parse the event dictionary

    """

    def __init__(self, event, context):
        self.region = os.environ['AWS_REGION']
        self.session = boto3.Session(region_name=self.region)
        self.asg = ASGWrapper(self.session)
        self.event = event
        self.context = context
        self.parser = AutoScalingEventParser(
            self.session, self.event, self.context)

    def start(self):
        """Tagger entry point

        This method is called by the lambda handler. It parses the event and tags the appropriate resources.

        Returns:
            dict: Response from AWS CreateOrUpdateTags API Call

        """
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
    """Lambda entry point

    This is the handler associated with this lambda function. It instantiates a new ASGTagger and passes
    down the event data.

    Args:
        event (dict): Event dictionary passed by AWS
        context (dict): Context dictionary passed by AWS (not used but required by AWS)

    Returns:
        dict: Response from AWS CreateOrUpdateTags API Call
    """
    return ASGTagger(event, context).start()
