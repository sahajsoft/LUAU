import boto3
from util.dynamo import EmailDynamoWrapper
from util.aws import SESWrapper


class Mailer(object):
    """
    The object controls the emailing functionality

    It fetches all the EC2 instances where email notifications have not
    been sent and send the emails based on the conditions and updates the
    dynamoDB
    """
