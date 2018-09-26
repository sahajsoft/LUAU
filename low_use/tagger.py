import boto3
import logging
import os
from util.aws import EC2Wrapper, DynamoWrapper, SESWrapper
from low_use.report_parser import LowUseReportParser

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LowUseTagger:
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

    def sync_whitelist(self):
        for instance in self.whitelist:
            self.dynamo.add_to_whitelist(instance['InstanceID'], instance['Creator'], instance['Reason'])

    def sync_low_use_instances(self): 
        for instance in self.low_use_instances:
            self.flag_instance_as_low_use(instance['InstanceID'], instance['Creator'])
        
    def sync_instances_scheduled_for_deletion(self):
        for instance in self.instances_scheduled_for_deletion:
            self.flag_instance_for_deletion(instance['InstanceID'], instance['Creator'])        
    
    def flag_instance_as_low_use(self, instance_id, creator):
        self.ec2.tag_as_low_use(instance_id)
        self.dynamo.add_to_low_use(instance_id, creator)

    def flag_instance_for_deletion(self, instance_id, creator): 
        self.ec2.tag_for_deletion(instance_id)
        self.dynamo.schedule_for_deletion(instance_id, creator)

    def sort_instances(self, instances):
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
                logger.info("Instance is already scheduled for deletion, doing nothing right now. In the future, instances will be stopped here")
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
        all_creators = set([instance['Creator'] for instance in self.low_use_instances])
        logger.info(all_creators)
        for creator in all_creators:
            yield {
                'creator': creator,
                'low_use': [instance for instance in self.low_use_instances if instance['Creator'] == creator],
                'scheduled_for_deletion': [instance for instance in self.instances_scheduled_for_deletion if instance['Creator'] == creator]
            }

    def start(self):
        report = self.parser.parse_low_use_report()
        self.sort_instances(report)

        #if self.instances_to_stop != []:
        #    self.ec2.stop_instances(instances_to_stop)
        #    self.dynamo.batch_delete_item_from_low_use(instances_to_stop)
        


        #for creator_report_data in self.get_creator_report():
            #response = self.ses.send_low_use_email(creator_report_data['creator'], creator_report_data['low_use'], creator_report_data['scheduled_for_deletion'])
    
        response = self.ses.send_admin_report(self.low_use_instances, self.instances_scheduled_for_deletion)
        logger.info(response)
        
        
    
def lambda_handler(event, context):
    return LowUseTagger(event, context).start()
