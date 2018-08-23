import boto3
import logging
from util.aws import EC2Wrapper, DynamoWrapper
from low_use.report_parser import LowUseReportParser

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LowUseTagger:
    def __init__(self, event, context):
        self.session = boto3.Session(region_name='us-west-2')
        self.ec2 = EC2Wrapper(self.session)
        self.dynamo = DynamoWrapper(self.session)
        self.event = event
        self.context = context
        self.parser = LowUseReportParser(self.session)
        self.whitelist = []
        self.low_use_instances = []
        self.instances_scheduled_for_deletion = []

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
            logger.info(instance)
            instance_id = instance['instance_id']
            creator = instance['creator']
            if self.ec2.is_whitelisted(instance_id):
                self.whitelist.append({
                    'InstanceID': instance_id,
                    'Creator': creator,
                    'Reason': self.ec2.get_whitelist_reason_for_instance(instance_id)
                })
            elif self.ec2.is_low_use(instance_id):
                self.instances_scheduled_for_deletion.append({
                    'InstanceID': instance_id,
                    'Creator': creator
                })
            elif self.ec2.is_scheduled_for_deletion(instance_id):
                logger.info("Instance is already scheduled for deletion, doing nothing right now. In the future, instances will be deleted here")
            else:
                self.low_use_instances.append({
                    'InstanceID': instance_id,
                    'Creator': creator
                })

    def start(self):
        report = self.parser.parse_low_use_report()
        self.sort_instances(report)
        logger.info(self.whitelist)
        logger.info(self.low_use_instances)
        logger.info(self.instances_scheduled_for_deletion)
        
    
def lambda_handler(event, context):
    return LowUseTagger(event, context).start()
