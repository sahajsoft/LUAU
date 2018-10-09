import unittest
import boto3
from moto import mock_autoscaling, mock_ec2, mock_dynamodb2, mock_ses
from util.aws import EC2Wrapper, ASGWrapper
class TestEC2Wrapper(unittest.TestCase):
    @mock_ec2
    def setUp(self):
        self.session = boto3.Session(region_name='us-west-2')
        self.wrapper = EC2Wrapper(self.session)
    
    def is_tagged_with_value(self, instance_name, response, tag_key, tag_value):
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance['InstanceId'] == instance_name:
                    for tag in instance['Tags']:
                        if tag['Key'] == tag_key and tag['Value'] == tag_value:
                            return True
        return False

    @mock_ec2
    def test_create_tags(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        test_tag = {
            'Key': 'test',
            'Value': 'test_value'
        }
        self.wrapper.create_tags(Resources=[instance], Tags=[test_tag])
        response = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        
        self.assertTrue(self.is_tagged_with_value(instance, response, 'test', 'test_value'))
        
    @mock_ec2
    def test_tag_as_low_use(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        response = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertFalse(self.is_tagged_with_value(instance, response, 'Low Use', 'true'))
        self.wrapper.tag_as_low_use(instance)
        response_after_tag = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertTrue(self.is_tagged_with_value(instance, response_after_tag, 'Low Use', 'true'))

    @mock_ec2
    def test_tag_as_whitelisted(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        response = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertFalse(self.is_tagged_with_value(instance, response, 'Whitelisted', 'true'))
        self.wrapper.tag_as_whitelisted(instance)
        response_after_tag = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertTrue(self.is_tagged_with_value(instance, response_after_tag, 'Whitelisted', 'true'))
    
    @mock_ec2
    def test_tag_whitelist_reason(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        response = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertFalse(self.is_tagged_with_value(instance, response, 'Reason', 'test_value'))
        self.wrapper.tag_whitelist_reason(instance, 'test_value')
        response_after_tag = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertTrue(self.is_tagged_with_value(instance, response_after_tag, 'Reason', 'test_value'))
    
    @mock_ec2
    def test_tag_for_deletion(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        response = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertFalse(self.is_tagged_with_value(instance, response, 'Scheduled For Deletion', 'true'))
        self.wrapper.tag_for_deletion(instance)
        response_after_tag = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertTrue(self.is_tagged_with_value(instance, response_after_tag, 'Scheduled For Deletion', 'true'))
    

    @mock_ec2
    def test_tag_instance(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        response = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertFalse(self.is_tagged_with_value(instance, response, 'test_key', 'test_value'))
        self.wrapper.tag_instance(instance, 'tag_key','test_value')
        response_after_tag = self.wrapper.ec2.describe_instances(InstanceIds=[instance])
        self.assertTrue(self.is_tagged_with_value(instance, response_after_tag, 'tag_key', 'test_value'))
    
    @mock_ec2
    def test_get_creator_for_instance(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        self.wrapper.tag_instance(instance, 'Creator','test_creator')
        self.assertEqual(self.wrapper.get_creator_for_instance(instance), 'test_creator')
    
    @mock_ec2
    def test_get_whitelist_reason_for_instance(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        self.wrapper.tag_as_whitelisted(instance)
        self.wrapper.tag_whitelist_reason(instance, 'test_value')
        self.assertEqual(self.wrapper.get_whitelist_reason_for_instance(instance), 'test_value')

    @mock_ec2
    def test_get_tag_for_instance(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        self.wrapper.tag_instance(instance, 'test_key', 'test_value')
        self.assertEqual(self.wrapper.get_tag_for_instance(instance, 'test_key'), 'test_value')

    @mock_ec2
    def test_get_tags_for_instance(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        self.wrapper.tag_instance(instance, 'test_key', 'test_value')
        expected = [{
            'Key': 'test_key',
            'Value': 'test_value'
        }]
        self.assertEqual(self.wrapper.get_tags_for_instance(instance), expected)

    @mock_ec2
    def test_is_whitelisted(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        self.wrapper.tag_as_whitelisted(instance)
        self.assertTrue(self.wrapper.is_whitelisted(instance))
    @mock_ec2
    def test_is_low_use(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        self.wrapper.tag_as_low_use(instance)
        self.assertTrue(self.wrapper.is_low_use(instance))

    @mock_ec2
    def test_is_scheduled_for_deletion(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        self.wrapper.tag_for_deletion(instance)
        self.assertTrue(self.wrapper.is_scheduled_for_deletion(instance))

    @mock_ec2
    def test_is_tagged(self):
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        self.wrapper.tag_instance(instance, 'test_key', 'true')
        self.assertTrue(self.wrapper.is_tagged(instance, 'test_key'))

class TestASGWrapper(unittest.TestCase):
    @mock_autoscaling
    def setUp(self):
        self.session = boto3.Session(region_name='us-west-2')
        self.wrapper = ASGWrapper(self.session)

    @mock_autoscaling
    def test_get_asg_user_tag_by_instance_id(self): 
        pass

class TestTrustedAdvisor(unittest.TestCase):
    pass

class TestDynamoWrapper(unittest.TestCase):
    pass

class TestSESWrapper(unittest.TestCase):
    pass