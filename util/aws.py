"""AWS Wrapper Module

This module contains wrapper classes for AWS Services. This includes:
    * EC2
    * AutoScaling
    * SES
    * TrustedAdvisor
    * DynamoDB

Attributes:
    LOW_USE_CHECK_ID (str): Unique str indentifier for Low Use Check in Trusted Advisor.
    SES_EMAIL (str): SES Email used to send Low Use reports from.
    ADMIN_EMAIL (str): Admin email account that will receive the admin reports.
"""

import boto3
import logging
import json

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

LOW_USE_CHECK_ID = 'Qch7DwouX1'
SES_EMAIL = 'keithw@sahajsoft.com'
ADMIN_EMAIL = 'keithw@sahajsoft.com'


class EC2Wrapper:
    """Wrapper for AWS EC2

    Attributes:
        session (obj): Boto3 Session object with AWS
        ec2 (obj): Boto3 EC2 Client object to directly interface with AWS EC2
    """
    def __init__(self, session):
        self.session = session
        self.ec2 = session.client('ec2')

    def create_tags(self, Resources, Tags):
        """Tags resources

        Args:
            Resources (:obj:`list` of :obj:`str`): List of Resource Ids
            Tags (:obj:`list` of :obj:`dict`): List of Key/Value pairs for Tags

        Returns:
            dict: response from AWS CreateTags API Call
        """
        return self.ec2.create_tags(
            Resources=Resources,
            Tags=Tags
        )

    def tag_as_low_use(self, instance_id):
        """Tag instance as Low Use

        Args:
            instance_id (str): ID of the Instance

        Returns:
            dict: response from AWS CreateTags API Call
        """
        return self.tag_instance(instance_id, 'Low Use', 'true')

    def tag_as_whitelisted(self, instance_id):
        """Tag instance as Whitelisted

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            dict: response from AWS CreateTags API Call
        """
        return self.tag_instance(instance_id, 'Whitelisted', 'true')

    def tag_whitelist_reason(self, instance_id, reason):
        """Tag instance with Whitelist Reason

        Args:
            instance_id (str): ID of the Instance
            reason (str): Reason for whitelisting, tag value
            
        Returns:
            dict: response from AWS CreateTags API Call
        """
        return self.tag_instance(instance_id, 'Reason', reason)

    def tag_for_deletion(self, instance_id):
        """Tag instance as Scheduled for Deletion

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            dict: response from AWS CreateTags API Call
        """
        return self.tag_instance(instance_id, 'Scheduled For Deletion', 'true')

    def tag_instance(self, instance_id, tag_key, tag_value):
        """Tag instance

        Args:
            instance_id (str): ID of the Instance
            tag_key (str): Key for the tag
            tag_value (str): value for the tag
        Returns:
            dict: response from AWS CreateTags API Call
        """
        tag = {
            'Key': tag_key,
            'Value': tag_value
        }
        return self.ec2.create_tags(
            Resources=[instance_id],
            Tags=[tag]
        )

    def get_creator_for_instance(self, instance_id):
        """Get the Creator tag value from instance

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            str: Creator of EC2 instance (Unknown if Creator tag does not exist)
        """
        return self.get_tag_for_instance(instance_id, 'Creator')

    def get_whitelist_reason_for_instance(self, instance_id):
        """Get the Reason tag value from instance

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            str: Reason for whitelisting the EC2 instance (None if Reason tag does not exist)
        """
        if self.is_whitelisted(instance_id):
            return self.get_tag_for_instance(instance_id, 'Reason')
        else:
            return None

    def get_tag_for_instance(self, instance_id, tag_key):
        """Get the specific tag value from instance

        Args:
            instance_id (str): ID of the Instance
            tag_key (str): key of the desired tag
            
        Returns:
            str: Value of desired tag of EC2 instance (None if tag does not exist)
        """
        tags = self.get_tags_for_instance(instance_id)
        for tag in tags:
            if tag['Key'] == tag_key:
                return tag['Value']
        return None

    def get_tags_for_instance(self, instance_id):
        """Get all tags from instance

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            list: all tags of EC2 instance (empty list if no tags exist)
        """
        response = self.ec2.describe_instances(InstanceIds=[instance_id])
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance['InstanceId'] == instance_id:
                    return instance['Tags']
        return []

    def is_whitelisted(self, instance_id):
        """Check if Instance is whitelisted

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            bool: True if whitelisted, false otherwise
        """
        return self.is_tagged(instance_id, 'Whitelisted')

    def is_low_use(self, instance_id):
        """Check if Instance is low use

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            bool: True if low use, false otherwise
        """
        return self.is_tagged(instance_id, 'Low Use')

    def is_scheduled_for_deletion(self, instance_id):
        """Check if Instance is scheduled for deletion

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            bool: True if scheduled for deletion, false otherwise
        """
        return self.is_tagged(instance_id, 'Scheduled For Deletion')

    def is_tagged(self, instance_id, tag_name):
        """Check if Instance is tagged with a specific key

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            bool: True if tagged, false otherwise
        """
        tag_value = self.get_tag_for_instance(instance_id, tag_name)
        if tag_value is not None and tag_value == 'true':
            return True
        else:
            return False

    def stop_instances(self, instance_ids): 
        """Stops instance

        Args:
            instance_id (str): ID of the Instance
            
        Returns:
            dict: Response from AWS StopInstances API call.
        """
        response = self.ec2.stop_instances(InstanceIds=instance_ids)
        logger.info(response)
        return response
        
class ASGWrapper:
    """Wrapper for AWS ASG

    Attributes:
        session (obj): Boto3 Session object with AWS
        asg (obj): Boto3 ASG Client object to directly interface with AWS ASG
    """
    def __init__(self, session):
        self.session = session
        self.asg = session.client('autoscaling')

    def get_asg_user_tag_by_instance_id(self, instance_ids):
        """Get the name of the ASG for these instances

        This is done to ensure that the owner of the ASG is accurated tagged as the owner
        of the instances belonging to the ASG

        Args:
            instance_ids ([str]): List of instance_ids that belong to the same ASG
        Returns:
            str: The ASG Name associated with these instances
        """
        # Use the first instance because all of them will belong to the same ASG
        instance_id = instance_ids[0]
        instance_data = self.asg.describe_auto_scaling_instances(InstanceIds=[instance_id])
        try:
            return instance_data['AutoScalingInstances'][0]['AutoScalingGroupName']
        except KeyError as e:
            logger.warning('Instance does not exist: %s', str(e))
        except Exception as e:
            logger.error('Unknown Error: %s', str(e))

    def get_asg_instance_ids(self, asg_name):
        """Get the instance_ids of instances belonging to an ASG

        Args:
            asg_name (str): Name of an ASG
        Returns:
            [str]: List of ids of instances in the ASG

        """
        instance_ids = []
        # Grab the first item in the list because we're only asking for 1 ASG
        asg_data = self.asg.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name])['AutoScalingGroups'][0]

        for instance_data in asg_data['Instances']:
            instance_ids.append(instance_data['InstanceId'])

        return instance_ids

    def create_or_update_tags(self, Tags):
        """Tag Autoscaling group and it's EC2 instances

        Args:
            Tags: (:obj:`list` of :obj:`dict`): List of tags to tag ASG and EC2

        Returns: 
            dict: Response from AWS EC2 CreateTags API Call

        """
        tag = Tags[0]
        asg_name = tag['ResourceId']
        ec2_tag = {
            'Key': tag['Key'],
            'Value': tag['Value']
        }
        try:
            response = self.asg.create_or_update_tags(
                Tags=Tags
            )
        except Exception as e:
            logger.error('Unknown Error: %s', str(e))
        else:
            logger.info(response)

        asg_instances = self.get_asg_instance_ids(asg_name)
        return EC2Wrapper(self.session).create_tags(Resources=asg_instances, Tags=[ec2_tag])


class TrustedAdvisor:
    """Wrapper for AWS ASG

    Attributes:
        support (obj): Boto3 Support Client object to directly interface with AWS TrustedAdvisor
    """
    def __init__(self):
        self.support = boto3.client('support', region_name='us-east-1')

    def get_low_use_instances(self):
        """Get low use instances

        Returns:
            :obj:`list` of :obj:`dict`: List of instances flagged as low use by TrustedAdvisor
        """
        response = self.support.describe_trusted_advisor_check_result(checkId=LOW_USE_CHECK_ID, language='en')
        if 'result' in response:
            return response['result'].get('flaggedResources', [])

    def get_low_use_summary(self):
        """Get low use report

        Returns:
            dict: Trusted Advisor Low Use Report, None if no report was pulled
        """
        response = self.support.describe_trusted_advisor_check_summaries(checkIds=[LOW_USE_CHECK_ID])
        for checks in response.get('summaries', []):
            if checks['checkId'] == LOW_USE_CHECK_ID:
                return checks
        return None


class SESWrapper:
    """Wrapper for AWS SES

    Attributes:
        session (obj): Boto3 Session object
        ses (obj): Boto3 SES Client
        low_use_template_name (str): Name of SES Template to use in the Low Use Report
        admin_template_name (str): Name of SES Template to use in the Admin Report
    """
    def __init__(self, session):
        self.session = session
        self.ses = session.client('ses')
        self.low_use_template_name = 'LowUseReport'
        self.admin_template_name = 'AdminLowUseReport'

    def get_low_use_template_data(self, creator, low_use_instances, instances_scheduled_for_deletion):
        """Creates the templated data to send via SES

        Args:
            creator (str): Person receiving email
            low_use_instances (:obj:`list` of :obj:`dict`): Has all low use instances and associated metadata
            instances_scheduled_for_deletion (:obj:`list` of :obj:`dict`): Has all scheduled for deletion instances and associated metadata
        Returns:
            dict: Template data to use in SES Email
        """
        template_data = {
            'creator': creator,
            'creator_name': creator.split('@')[0],
            'instance': []
        }

        for instance in low_use_instances:
            if instance['Creator'] is None:
                instance['Creator'] = 'Unknown'
            instance_data = {
                'instance_id': instance['InstanceID'],
                'instance_creator': instance['Creator'],
                'scheduled_for_deletion': False,
                'cost': instance['Cost'],
                'average_cpu_usage': instance['AverageCpuUsage'],
                'average_network_usage': instance['AverageNetworkUsage']
            }
            template_data['instance'].append(instance_data)

        for instance in instances_scheduled_for_deletion:
            if instance['Creator'] is None:
                instance['Creator'] = 'Unknown'
            instance_data = {
                'instance_id': instance['InstanceID'],
                'instance_creator': instance['Creator'],
                'scheduled_for_deletion': True,
                'cost': instance['Cost'],
                'average_cpu_usage': instance['AverageCpuUsage'],
                'average_network_usage': instance['AverageNetworkUsage']
            }
            template_data['instance'].append(instance_data)

        return template_data

    def send_low_use_email(self, creator, low_use_instances, instances_scheduled_for_deletion, TemplateName=None):
        """Sends the low use report

        Args:
            creator (str, optional): Email of the instances owner. If not given, will send to Admin
            low_use_instances (:obj:`list` of :obj:`dict`): Has all low use instances and associated metadata
            instances_scheduled_for_deletion (:obj:`list` of :obj:`dict`): Has all scheduled for deletion instances and associated metadata
            TemplateName (str, optional): SES template to use, must be created in your AWS Account. If none specified, will use Low Use template.

        Returns:
            dict: Response from AWS SES SendTemplatedEmail API Call
        """
        if creator is None:
            creator = ADMIN_EMAIL
        if TemplateName is None:
            template_name = self.low_use_template_name
        else:
            template_name = TemplateName

        source = SES_EMAIL
        destination = {
            'ToAddresses':[creator]
        }
        template_data = self.get_low_use_template_data(creator,
                                                       low_use_instances,
                                                       instances_scheduled_for_deletion)
        template_data_json = json.dumps(template_data)
        logger.info(template_data)
        response = self.ses.send_templated_email(
            Source=source,
            Destination=destination,
            Template=template_name,
            TemplateData=template_data_json
        )
        return response

    def send_admin_report(self, low_use_instances, instances_scheduled_for_deletion):
        """Sends the admin report

        Args:
            low_use_instances (:obj:`list` of :obj:`dict`): Has all low use instances and associated metadata
            instances_scheduled_for_deletion (:obj:`list` of :obj:`dict`): Has all scheduled for deletion instances and associated metadata

        Returns:
            dict: Response from AWS SES SendTemplatedEmail API Call
        """
        return self.send_low_use_email(ADMIN_EMAIL, low_use_instances,
                                       instances_scheduled_for_deletion,
                                       TemplateName=self.admin_template_name)
class DynamoWrapper(object):
    """Handler for dynamodb data

    Attributes:
        session (obj): Boto3 AWS Session Object
        dynamo (obj): Boto3 AWS Dynamo Resource Object
        low_use (obj): Boto3 AWS Dynamo Table Object
        whitelist (obj): Boto3 AWS Dynamo Table Object

    """
    def __init__(self, session):
        self.session = session
        self.dynamo = session.resource('dynamodb')
        self.low_use = self.dynamo.Table('LowUse')
        self.whitelist = self.dynamo.Table('Whitelist')

    def get_whitelist_instance(self, instance_id):
        """Fetch Instance from whitelist table.

        Args:
            instance_id (str): ID of EC2 Instance

        Returns:
            dict: DynamoDB item from Whitelist table. None if item does not exist
        """
        key = {"InstanceID": instance_id}
        return self.whitelist.get_item(Key=key)

    def get_low_use_instance(self, instance_id):
        """Fetch Instance from low use table.

        Args:
            instance_id (str): ID of EC2 Instance

        Returns:
            dict: DynamoDB item from LowUse table. None if item does not exist
        """
        key = {"InstanceID": instance_id}
        return self.low_use.get_item(Key=key)

    def is_whitelisted(self, instance_id):
        """Checks if an instance is whitelisted in Dynamo

        Args:
            instance_id (str): ID of EC2 Instance

        Returns:
            bool: True if instance is whitelisted, false otherwise
        """
        item = self.get_whitelist_instance(instance_id)
        if item is None:
            return False
        else:
            return True

    def is_low_use(self, instance_id):
        """Checks if an instance is flagged as low use in Dynamo

        Args:
            instance_id (str): ID of EC2 Instance

        Returns:
            bool: True if instance is low use, false otherwise
        """
        item = self.get_low_use_instance(instance_id)
        if item is None:
            return False
        else:
            return True

    def is_scheduled_for_deletion(self, instance_id):
        """Checks if an instance is scheduled for deletion in Dynamo

        Args:
            instance_id (str): ID of EC2 Instance

        Returns:
            bool: True if instance is scheduled for deletion, false otherwise
        """
        item = self.get_low_use_instance(instance_id)
        if item is not None:
            return item.get('Scheduled For Deletion', False)

    def add_to_whitelist(self, instance_id, creator, reason):
        """Adds an instance to the whitelist

        Args:
            instance_id (str): ID of EC2 Instance
            creator (str): Creator email of Instance
            reason (str): Reason for Whitelisting

        Returns:
            dict: Response from AWS DynamoDB PutItem API Call
        """
        item = {
            "InstanceID": instance_id,
            "Creator": creator,
            "Reason": reason,
            "EmailSent": False
        }
        self.delete_from_low_use(instance_id)
        response = self.whitelist.put_item(Item=item)
        return response

    def add_to_low_use(self, instance_id, creator):
        """Adds an instance to the low use list

        Args:
            instance_id (str): ID of EC2 Instance
            creator (str): Creator email of Instance

        Returns:
            dict: Response from AWS DynamoDB PutItem API Call
        """
        item = {
            "InstanceID": instance_id,
            "Creator": creator,
            "Scheduled For Deletion": False,
            "EmailSent": False
        }

        return self.low_use.put_item(Item=item)

    def schedule_for_deletion(self, instance_id, creator):
        """Adds an instance to the low use list and labels it as scheduled for deletion

        Args:
            instance_id (str): ID of EC2 Instance
            creator (str): Creator email of Instance

        Returns:
            dict: Response from AWS DynamoDB PutItem API Call
        """
        item = {
            "InstanceID": instance_id,
            "Creator": creator,
            "Scheduled For Deletion": True
        }

        return self.low_use.put_item(Item=item)

    def delete_from_low_use(self, instance_id):
        """Removes an instance from the low use list

        Args:
            instance_id (str): ID of EC2 Instance

        Returns:
            dict: Response from AWS DynamoDB DeleteItem API Call
        """
        key = {"InstanceID": instance_id}
        return self.low_use.delete_item(Key=key)

    def batch_delete_item_from_low_use(self, instance_ids): 
        """Removes multiple instances from the low use list

        Args:
            instance_ids (:obj:`list` of :obj:`str`): IDs of EC2 Instance
        """
        for instance_id in instance_ids:
            self.delete_from_low_use(instance_id)


class EmailDynamoWrapper(DynamoWrapper):
    """Extends the DynamoWrapper to handle email queries

    We want to get instances where EmailSet is set to False for
    LowUse table and whitelisted table

    Attributes:
        type_map (dict): dict that determines which DynamoDB table 
            to use based off of the instance state (Low Use or Whitelisted)
    """

    def __init__(self, session):
        super(EmailDynamoWrapper).__init__(session)
        self.type_map = {"low_use": self.low_use,
                         "whitelist": self.whitelist}

    def get_low_use_instances(self):
        """Fetch instances from whitelist table

        Returns: 
            dict: Response from the AWS DynamoDB BatchGetItem API Call
        """
        return self.low_use.batch_get_item(EmailSent=True)

    def get_whitelist_instances(self):
        """Fetch Instances from whitelist table.

        Returns: 
            dict: Response from the AWS DynamoDB BatchGetItem API Call
        """
        return self.whitelist.batch_get_item(EmailSent=True)

    def set_email_sent(self, instance_id, creator, type):
        """Set EmailSent key value to True after email is sent.

        Args:
            instance_id (str): ID of EC2 Instance
            creator (str): Creator email of Instance
            type: (str): Whether or not an instance was whitelisted or low use
        
        Returns: 
            dict: Response from the AWS DyanmoDB PutItem API Call
        """
        table = self.type_map[type]
        item = {
                "InstanceID": instance_id,
                "Creator": creator,
                "Scheduled For Deletion": True,
                "EmailSent": True
                }
        return table.put_item(item)

