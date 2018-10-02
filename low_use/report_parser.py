"""Parses the Low Use report

This module parses the Low Use Report from AWS Trusted Advisor, and 
grabs some instance metadata from EC2 such as tags
"""

import logging
from util.aws import TrustedAdvisor, EC2Wrapper

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LowUseReportParser:
    """Parses the Low Use report

    Attributes:
        session (obj): Boto3 AWS Session Object
        advisor (obj): Wrapper for AWS TrustedAdvisor
        ec2 (obj): Wrapper for AWS EC2
    """
    def __init__(self, session):
        self.session = session
        self.advisor = TrustedAdvisor()
        self.ec2 = EC2Wrapper(session)

    def parse_low_use_report(self): 
        """Parses the report

        Returns:   
            list of dict: List of Low use instances with associated metadata
        """
        report = self.advisor.get_low_use_instances()
        list_of_instances = []
        for instance in report:
            instance_metadata = self.parse_metadata(instance['metadata'])
            list_of_instances.append(instance_metadata)
        return list_of_instances

    def parse_metadata(self, metadata):
        """Parses instance metadata

        This function mainly formats the metadata to use key/value pairs instead of indexing for
        a better understanding of what the metadata is further downstream

    
        Args:
            metadata (:obj:`list`): Metadata from Low Use report

        Returns:
            dict: Metadata of instance
        """
        creator = self.ec2.get_creator_for_instance(metadata[1])
        if creator is None: 
            return []
        usage_logs = metadata[5:19]
        instance_usage = self.parse_instance_usage(usage_logs)
        instance_metadata = {
            'creator': creator,
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
        """Parsess instance usage

        Args:
            usage_logs (:obj:`list` of :obj:`str`): List of unformatted usage over at most 2 weeks

        Returns:
            list: lists of CPU usage and network IO over the given time frame.
        """
        cpu_usage_over_time = []
        network_io_over_time = []
        for day in usage_logs:
            if day is None: continue
            usage = day.split(' ')
            cpu_usage_over_time.append(usage[0])
            network_io_over_time.append(usage[2])
        return cpu_usage_over_time, network_io_over_time

    def get_number_of_days(self, day_string):
        """Get number of days in report

        Used to determine how many days the instance has data for

        Args:
            day_string (str): String that has the amount of days

        Returns:
            int: number of days with data
        """
        return int(day_string.split(' ')[0])
