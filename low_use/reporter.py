"""Lambda Function to parse Low Use Report and send email reports

This function grabs and parses the Low Use report from AWS TrustedAdvisor, flags
instances as either Whitelisted, Low Use, or Scheduled for Deletion via Tagging
and DynamoDB Tables, and then sends Low Use/Admin report emails to the given 
users.
"""


import boto3
import logging
import os
from util.aws import EC2Wrapper, DynamoWrapper, SESWrapper
from low_use.report_parser import LowUseReportParser

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LowUseReporter:
    """Parses the Low Use report, sync instance states with Dynamo, and sends email reports

    Attrbiutes:
        session (obj): Boto3 AWS Session Object
        ec2 (obj) Wrapper for AWS EC2
        dynamo (obj): Wrapper for AWS DynamoDB
        ses (obj): Wrapper for AWS SES
        event (dict): Event dictionary passed by Lambda trigger
        context (dict): Context dictionary passed by Lambda trigger
        parser (obj): Parses the Low Use Report
        whitelist (:obj:`list` of :obj:`dict`): list of whitelisted instances and associated metadata 
        low_use_instances (:obj:`list` of :obj:`dict`): list of low_use instances and associated metadata 
        instances_scheduled_for_deletion (:obj:`list` of :obj:`dict`): list of instances scheduled for deletion and associated metadata 
        instances_to_stop (:obj:`list` of :obj:`dict`): list of instances to be stopped and associated metadata 
    """
    def __init__(self, event, context):
        self.session = boto3.Session(region_name=os.environ['AWS_REGION'])
        self.ec2 = EC2Wrapper(self.session)
        self.dynamo = DynamoWrapper(self.session)
        self.ses = SESWrapper(self.session)
        self.event = event
        self.context = context
        self.parser = LowUseReportParser(self.session)
        self.whitelist = []
        self.low_use_instances = []
        self.instances_scheduled_for_deletion = []
        self.instances_to_stop = []


    def sync(self): 
        self.sync_whitelist()
        self.sync_low_use_instances()
        self.sync_instances_scheduled_for_deletion()

    def sync_whitelist(self):
        """Sync whitelist
        
        Adds newly whitelisted instances to the Whitelist DynamoDB Table
        """
        for instance in self.whitelist:
            self.dynamo.add_to_whitelist(instance['InstanceID'], instance['Creator'], instance['Reason'])

    def sync_low_use_instances(self): 
        """Sync low_use instances
        
        Flags instances as low use and adds them to the LowUse DynamoDB Table
        """
        for instance in self.low_use_instances:
            self.flag_instance_as_low_use(instance['InstanceID'], instance['Creator'])
        
    def sync_instances_scheduled_for_deletion(self):
        """Sync instances scheduled for deletion
        
        Flags instances as scheduled for deletion and sets them as such in the LowUse DynamoDB Table
        """
        for instance in self.instances_scheduled_for_deletion:
            self.flag_instance_for_deletion(instance['InstanceID'], instance['Creator'])        
    
    def flag_instance_as_low_use(self, instance_id, creator):
        """Flag an instance as low_use

        Flags an instance as low use via tags and in the a DynamoDB Table

        Args:
            instance_id (str): ID of EC2 Instance
            creator (str): creator of EC2 Instance
        """
        self.ec2.tag_as_low_use(instance_id)
        self.dynamo.add_to_low_use(instance_id, creator)

    def flag_instance_for_deletion(self, instance_id, creator): 
        """Flag an instance as scheduled for deletion

        Flags an instance as scheduled for deletion via tags and in the a DynamoDB Table

        Args:
            instance_id (str): ID of EC2 Instance
            creator (str): creator of EC2 Instance
        """
        self.ec2.tag_for_deletion(instance_id)
        self.dynamo.schedule_for_deletion(instance_id, creator)

    def sort_instances(self, instances):
        """Sort instances from Low Use Report

        Sorts the instances flagged by TrustedAdvisor as either:
            * Whitelisted (Will never be stopped)
            * Low Use (2 weeks from stopped)
            * Scheduled For Deletion (1 week from stopped)
            * To Be Stopped Immediately (Stopped in this invocation)

        Args:
            instances (:obj:`list` of :obj:`dict`): List of instances flagged by TrustedAdvisor and associated metadata

        """
        for instance in instances:
            instance_id = instance['instance_id']
            creator = instance['creator']
            cost = instance['cost']
            cpu_average = instance['cpu_average']
            network_average = instance['network_average']
            if self.ec2.is_whitelisted(instance_id):
                self.whitelist.append({
                    'InstanceID': instance_id,
                    'Creator': creator,
                    'Reason': self.ec2.get_whitelist_reason_for_instance(instance_id)
                })
            elif self.ec2.is_low_use(instance_id):
                self.instances_scheduled_for_deletion.append({
                    'InstanceID': instance_id,
                    'Creator': creator,
                    'Cost': cost,
                    'AverageCpuUsage': cpu_average,
                    'AverageNetworkUsage': network_average
                })
            elif self.ec2.is_scheduled_for_deletion(instance_id):
                self.instances_to_stop.append(instance_id)
            else:
                self.low_use_instances.append({
                    'InstanceID': instance_id,
                    'Creator': creator,
                    'Cost': cost,
                    'AverageCpuUsage': cpu_average,
                    'AverageNetworkUsage': network_average
                })

    def get_creator_report(self):
        """Generates creator reports

        Generates a new report for each creator with associated low use instances

        Yields:
            dict: creator report for each creator with associated low use instances
        """
        all_creators = set([instance['Creator'] for instance in self.low_use_instances])
        logger.info(all_creators)
        for creator in all_creators:
            yield {
                'creator': creator,
                'low_use': [instance for instance in self.low_use_instances if instance['Creator'] == creator],
                'scheduled_for_deletion': [instance for instance in self.instances_scheduled_for_deletion if instance['Creator'] == creator]
            }

    def start(self):
        """Lambda entry point

        This is where the Lambda invocation starts. It parses the low use reports, sorts the instances
        and sends creator/admin email reports.
        """
        report = self.parser.parse_low_use_report()
        self.sort_instances(report)
        self.sync()

        if self.instances_to_stop != []:
            logger.warning("Stopping the following instances: %s", self.instances_to_stop)
            self.ec2.stop_instances(self.instances_to_stop)
            self.dynamo.batch_delete_item_from_low_use(self.instances_to_stop)
        


        for creator_report_data in self.get_creator_report():
            response = self.ses.send_low_use_email(creator_report_data['creator'], creator_report_data['low_use'], creator_report_data['scheduled_for_deletion'])
    
        response = self.ses.send_admin_report(self.low_use_instances, self.instances_scheduled_for_deletion)
        logger.info(response)
        
        
    
def lambda_handler(event, context):
    """Lambda handler

    This is the handler for the Lambda environment, and kicks off the process
    
    Args:
        event (dict): Event dictionary passed by Lambda trigger
        context (dict): Context dictionary passed by Lambda trigger
    """
    return LowUseReporter(event, context).start()
