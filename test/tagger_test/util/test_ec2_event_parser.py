import unittest
import boto3
from moto import mock_ec2
from tagger.util.ec2_event_parser import EC2EventParser


class TestEC2EventParser(unittest.TestCase):
    def setUp(self):
        self.parser = EC2EventParser(None, None, None)

    def test_get_username(self):
        event = {
            'userIdentity': {
                'userName': 'Test'
            }

        }

        event_without_username = {

            'userIdentity': {
            }

        }
        self.parser.event = event
        self.assertEqual(self.parser.get_username(), 'Test')
        self.parser.event = event_without_username
        self.assertEqual(self.parser.get_username(), 'None')

    def test_get_event_name(self):
        event = {
            'detail': {
                'eventName': 'Test'
            }
        }

        event_without_eventname = {
            'detail': {
            }
        }
        self.parser.event = event
        self.assertEqual(self.parser.get_event_name(), 'Test')
        self.parser.event = event_without_eventname
        self.assertEqual(self.parser.get_event_name(), 'None')

    def test_get_created_instance_ids(self):
        event = {
            'detail': {
                'responseElements': {
                    'instancesSet': {
                        'items': [
                            {
                                'instanceId': 'test1'
                            },
                            {
                                'instanceId': 'test2'
                            }
                        ]

                    }
                }
            }
        }
        event_without_instances = {
            'detail': {'responseElements': {'instancesSet':{'items':[]}}}
        }
        expected_instances = ['test1', 'test2']
        self.parser.event = event
        self.assertEqual(self.parser.get_created_instance_ids(), expected_instances)
        self.parser.event = event_without_instances
        self.assertEqual(self.parser.get_created_instance_ids(), [])

    def test_get_resource_ids(self):
        instance_event = {
            'detail': {
                'responseElements': {
                    'instancesSet': {
                        'items': [
                            {
                                'instanceId': 'test1'
                            },
                            {
                                'instanceId': 'test2'
                            }
                        ]

                    }
                }
            }
        }

        sg_event = {
            'detail':{
                'responseElements':{
                    'groupId': 'test-sec'
                }
            }
        }

        ami_event ={
            'detail':{
                'responseElements':{
                    'imageId': 'test-image'
                }
            }
        }

        ebs_event = {
            'detail':{
                'responseElements':{
                    'volumeId': 'test-volume'
                }
            }
        }

        self.parser.event = instance_event
        expected_resources = ['test1', 'test2']
        self.assertEqual(self.parser.get_resource_ids('RunInstances'), expected_resources)
        self.parser.event = sg_event
        self.assertEqual(self.parser.get_resource_ids('CreateSecurityGroup'), ['test-sec'])
        self.parser.event = ami_event
        self.assertEqual(self.parser.get_resource_ids('CreateImage'), ['test-image'])
        self.parser.event = ebs_event
        self.assertEqual(self.parser.get_resource_ids('CreateVolume'), ['test-volume'])
