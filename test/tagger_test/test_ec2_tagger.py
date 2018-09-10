import unittest
import json
import boto3
import os
from mock import MagicMock
from moto import mock_autoscaling, mock_ec2
from tagger.ec2_tagger import EC2Tagger

class TestEC2Tagger(unittest.TestCase):
    
    @mock_ec2
    def setUp(self):
        json_data = open('./test/example_events/run_instances.json').read()
        self.event = json.loads(json_data)
        self.region = 'us-west-2'
        os.environ['AWS_REGION'] = 'us-west-2'
        
    
    @mock_ec2
    def test_start(self):
        self.tagger = EC2Tagger(self.event, None)
        response = self.tagger.start()
        response_metadata = response['ResponseMetadata']
        self.assertEqual(response_metadata['HTTPStatusCode'], 200)