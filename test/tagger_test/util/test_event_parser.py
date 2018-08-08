import unittest
import boto3
from moto import mock_ec2
from tagger.util.event_parser import AWSEventParser


class TestAWSEventParser(unittest.TestCase):
    def setUp(self):
        self.parser = AWSEventParser(None, None, None)

    def test_get_username(self):
        event = {
            'detail': {
                'userIdentity': {
                    'userName': 'Test'
                }
            }
        }

        event_without_username = {
            'detail': {
                'userIdentity': {
                }
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
