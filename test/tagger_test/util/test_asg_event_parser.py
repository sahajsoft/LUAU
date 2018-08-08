import unittest
import json
from tagger.util.asg_event_parser import AutoScalingEventParser

class TestAutoScalingEventParser(unittest.TestCase):
    def setUp(self):
        self.parser = AutoScalingEventParser(None, None, None)

    def test_get_asg_name(self):
        event = {
            'detail':{
                'requestParameters':{
                    'autoScalingGroupName': 'test'
                }
            }
        }

        self.parser.event = event
        self.assertEqual(self.parser.get_asg_name(), 'test')

    def test_parse_event(self):
        event = {
            'detail':{
                'userIdentity': {
                    'userName': 'Test'
                },
                'requestParameters':{
                    'autoScalingGroupName': 'test_asg'
                }
            }
        }
        expected_response = ('Test', 'test_asg')
        self.parser.event = event
        self.assertEqual(expected_response, self.parser.parse_event())

    def test_parse_event_json(self):
        json_data = open('./test/example_events/create_asg.json').read()
        event = json.loads(json_data)
        self.parser.event = event
        expected_response = ('keithw@sahajsoft.com', 'test_asg_LUAU')
        self.assertEqual(expected_response, self.parser.parse_event())
