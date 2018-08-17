import unittest
import boto3
from moto import mock_ec2
import json
from tagger.parser.ec2_event import EC2EventParser


class TestEC2EventParser(unittest.TestCase):
    def setUp(self):
        self.parser = EC2EventParser(None, None, None)

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
            'detail': {'responseElements': {'instancesSet': {'items': []}}}
        }
        expected_instances = ['test1', 'test2']
        self.parser.event = event
        self.assertEqual(
            self.parser.get_created_instance_ids(), expected_instances)
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
            'detail': {
                'responseElements': {
                    'groupId': 'test-sec'
                }
            }
        }

        ami_event = {
            'detail': {
                'responseElements': {
                    'imageId': 'test-image'
                }
            }
        }

        ebs_event = {
            'detail': {
                'responseElements': {
                    'volumeId': 'test-volume'
                }
            }
        }

        self.parser.event = instance_event
        expected_resources = ['test1', 'test2']
        self.assertEqual(self.parser.get_resource_ids(
            'RunInstances'), expected_resources)
        self.parser.event = sg_event
        self.assertEqual(self.parser.get_resource_ids(
            'CreateSecurityGroup'), ['test-sec'])
        self.parser.event = ami_event
        self.assertEqual(self.parser.get_resource_ids(
            'CreateImage'), ['test-image'])
        self.parser.event = ebs_event
        self.assertEqual(self.parser.get_resource_ids(
            'CreateVolume'), ['test-volume'])

    def test_invoked_by_asg(self):
        event = {
            'detail': {
                'userIdentity': {
                    'invokedBy': 'autoscaling.amazonaws.com'
                }
            }
        }
        self.parser.event = event
        self.assertTrue(self.parser.invoked_by_asg())
        event_not_invoked = {
            'detail': {
                'userIdentity': {
                    'invokedBy': 'somethingelse.amazonaws.com'
                }
            }
        }
        self.parser.event = event_not_invoked
        self.assertFalse(self.parser.invoked_by_asg())

        self.parser.event = {}
        self.assertFalse(self.parser.invoked_by_asg())

    def test_parse_event(self):
        full_event = {
            'detail': {
                'eventName': 'RunInstances',
                'userIdentity': {
                    'userName': 'Test'
                },
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
        expected_instances = ['test1', 'test2']
        self.parser.event = full_event
        username, resource_ids = self.parser.parse_event()
        self.assertEqual(username, 'Test')
        self.assertEqual(resource_ids, expected_instances)

    def test_parse_event_json(self):
        json_data = open('./test/example_events/run_instances.json').read()
        event = json.loads(json_data)
        self.parser.event = event
        expected_response = ('sahajsoft', ['i-092a8256362fcb350'])
        self.assertEqual(self.parser.parse_event(), expected_response)

