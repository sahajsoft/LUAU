import logging
from util.aws import TrustedAdvisor, EC2Wrapper

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LowUseReportParser:
    def __init__(self, session):
        self.session = session
        self.advisor = TrustedAdvisor()
        self.ec2 = EC2Wrapper(session)

    def parse_low_use_report(self): 
        report = self.advisor.get_low_use_instances()
        list_of_instances = []
        for instance in report:
            instance_metadata = self.parse_metadata(instance['metadata'])
            list_of_instances.append(instance_metadata)
        return list_of_instances

    def parse_metadata(self, metadata):
        usage_logs = metadata[5:19]
        instance_usage = self.parse_instance_usage(usage_logs)
        instance_metadata = {
            'creator': self.ec2.get_creator_for_instance(metadata[1]),
            'region': metadata[0],
            'instance_id': metadata[1],
            'instance_name': metadata[2],
            'instance_type': metadata[3],
            'cost': metadata[4],
            'cpu_usage': instance_usage[0],
            'network_usage': instance_usage[1],
            'cpu_average': metadata[-3],
            'network_average': metadata[-2],
            'days_logged': self.get_number_of_days(metadata[-1])
        }
        return instance_metadata

    def parse_instance_usage(self, usage_logs): 
        cpu_usage_over_time = []
        network_io_over_time = []
        for day in usage_logs:
            if day is None: continue
            usage = day.split(' ')
            cpu_usage_over_time.append(usage[0])
            network_io_over_time.append(usage[2])
        return cpu_usage_over_time, network_io_over_time

    def get_number_of_days(self, day_string):
        return int(day_string.split(' ')[0])
