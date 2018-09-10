import unittest
import json
import boto3
import os
from mock import MagicMock
from moto import mock_autoscaling, mock_ec2
from tagger.asg_tagger import ASGTagger

class TestASGTagger(unittest.TestCase):
    
    @mock_autoscaling
    def setUp(self):
        json_data = open('./test/example_events/create_asg.json').read()
        self.event = json.loads(json_data)
        self.region = 'us-west-2'
        os.environ['AWS_REGION'] = 'us-west-2'
        
    
    @mock_autoscaling
    @mock_ec2
    def test_start(self):
        self.tagger = ASGTagger(self.event, None)
        self.asg = boto3.client('autoscaling', region_name=self.region)
        self.asg.create_launch_configuration(LaunchConfigurationName='test_asg_config')
        self.asg.create_auto_scaling_group(AutoScalingGroupName='test_asg_LUAU', LaunchConfigurationName='test_asg_config', MinSize=1, MaxSize=1, AvailabilityZones=[self.region])
        response = self.tagger.start()
        response_metadata = response['ResponseMetadata']
        self.assertEqual(response_metadata['HTTPStatusCode'], 200)