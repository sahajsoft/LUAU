import unittest
import boto3
from moto import mock_dynamodb2, mock_ec2
from low_use.reporter import LowUseReporter
from util.aws import EC2Wrapper, DynamoWrapper
import os


class TestLowUseReporter(unittest.TestCase):
    @mock_dynamodb2
    @mock_ec2
    def setUp(self):
        self.session = boto3.Session(region_name='us-west-2')
        self.wrapper = EC2Wrapper(self.session)
        self.dynamo = DynamoWrapper(self.session)

        os.environ['AWS_REGION'] = 'us-west-2'
        self.reporter = LowUseReporter(None, None)
        self.maxDiff = None
        self.dynamo_resource = boto3.resource(
            'dynamodb', region_name='us-west-2')

    @mock_dynamodb2
    def create_tables(self):
        self.whitelist_table = self.dynamo_resource.create_table(
            TableName='Whitelist',
            KeySchema=[
                {
                    'AttributeName': 'InstanceID',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'InstanceID',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'Creator',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'Reason',
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )
        self.lowuse_table = self.dynamo_resource.create_table(
            TableName='LowUse',
            KeySchema=[
                {
                    'AttributeName': 'InstanceID',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'InstanceID',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'Creator',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'Scheduled For Deletion',
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )
        self.lowuse_table.meta.client.get_waiter(
            'table_exists').wait(TableName='LowUse')
        self.whitelist_table.meta.client.get_waiter(
            'table_exists').wait(TableName='Whitelist')
        self.dynamo.low_use = self.dynamo_resource.Table('LowUse')
        self.dynamo.whitelist = self.dynamo_resource.Table('Whitelist')

    def test_sync(self):
        pass

    @mock_dynamodb2
    def test_sync_whitelist(self):
        self.create_tables()

        test_item = {
            'InstanceID': 'test_id',
            'Creator': 'test_creator',
            'Reason': 'test_reason',
            'EmailSent': False
        }
        self.reporter.whitelist.append(test_item)
        self.reporter.sync_whitelist()
        item = self.whitelist_table.get_item(
            Key={'InstanceID': 'test_id'})['Item']
        self.assertDictEqual(test_item, item)

    @mock_dynamodb2
    @mock_ec2
    def test_sync_low_use_instances(self):
        self.create_tables()
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)[
            'Instances'][0]['InstanceId']
        test_item = {
            'InstanceID': instance,
            'Creator': 'test_creator',
            'Scheduled For Deletion': False,
            'EmailSent': False
        }

        self.reporter.low_use_instances.append(test_item)
        self.reporter.sync_low_use_instances()
        item = self.lowuse_table.get_item(Key={'InstanceID': instance})['Item']
        self.assertDictEqual(test_item, item)
        self.assertTrue(self.wrapper.is_low_use(instance))

    @mock_dynamodb2
    @mock_ec2
    def test_sync_instances_scheduled_for_deletion(self):
        self.create_tables()
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)[
            'Instances'][0]['InstanceId']
        test_item = {
            'InstanceID': instance,
            'Creator': 'test_creator',
            'Scheduled For Deletion': True,
        }

        self.reporter.instances_scheduled_for_deletion.append(test_item)
        self.reporter.sync_instances_scheduled_for_deletion()
        item = self.lowuse_table.get_item(Key={'InstanceID': instance})['Item']
        self.assertDictEqual(test_item, item)
        self.assertTrue(self.wrapper.is_scheduled_for_deletion(instance))

    @mock_dynamodb2
    @mock_ec2
    def test_flag_instances_as_low_use(self):
        self.create_tables()
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)[
            'Instances'][0]['InstanceId']
        test_item = {
            'InstanceID': instance,
            'Creator': 'test_creator',
            'Scheduled For Deletion': False,
            'EmailSent': False
        }

        self.reporter.flag_instance_as_low_use(instance, 'test_creator')
        item = self.lowuse_table.get_item(Key={'InstanceID': instance})['Item']
        self.assertDictEqual(test_item, item)
        self.assertTrue(self.wrapper.is_low_use(instance))

    @mock_dynamodb2
    @mock_ec2
    def test_flag_instance_for_deletion(self):
        self.create_tables()
        instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)[
            'Instances'][0]['InstanceId']
        test_item = {
            'InstanceID': instance,
            'Creator': 'test_creator',
            'Scheduled For Deletion': True,
        }

        self.reporter.flag_instance_for_deletion(instance, 'test_creator')
        item = self.lowuse_table.get_item(Key={'InstanceID': instance})['Item']
        self.assertDictEqual(test_item, item)
        self.assertTrue(self.wrapper.is_scheduled_for_deletion(instance))

    @mock_ec2
    def test_sort_instances(self):
        whitelist_instance = self.wrapper.ec2.run_instances(
            MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        instance_to_stop = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)[
            'Instances'][0]['InstanceId']
        low_use_instance = self.wrapper.ec2.run_instances(MaxCount=1, MinCount=1)[
            'Instances'][0]['InstanceId']
        schedule_to_delete_instance = self.wrapper.ec2.run_instances(
            MaxCount=1, MinCount=1)['Instances'][0]['InstanceId']
        self.wrapper.tag_as_low_use(schedule_to_delete_instance)
        self.wrapper.tag_as_whitelisted(whitelist_instance)
        self.wrapper.tag_for_deletion(instance_to_stop)

        list_of_instances = [{
            'instance_id': whitelist_instance
        }, {
            'instance_id': low_use_instance
        }, {
            'instance_id': instance_to_stop
        }, {
            'instance_id': schedule_to_delete_instance
        },
        ]

        expected_whitelist = [
            {
                'InstanceID': whitelist_instance,
                'Creator': 'Unknown',
                'Reason': None
            }
        ]

        expected_instances_to_stop = [instance_to_stop]

        expected_low_use_list = [{
            'InstanceID': low_use_instance,
            'Creator': 'Unknown',
            'Cost': 'Unknown',
            'AverageCpuUsage': 'Unknown',
            'AverageNetworkUsage': 'Unknown'
        }]

        expected_delete_list = [{
            'InstanceID': schedule_to_delete_instance,
            'Creator': 'Unknown',
            'Cost': 'Unknown',
            'AverageCpuUsage': 'Unknown',
            'AverageNetworkUsage': 'Unknown'
        }]

        self.reporter.sort_instances(list_of_instances)

        self.assertEqual(expected_whitelist, self.reporter.whitelist)
        self.assertEqual(expected_low_use_list,
                         self.reporter.low_use_instances)
        self.assertEqual(expected_delete_list,
                         self.reporter.instances_scheduled_for_deletion)
        self.assertEqual(expected_instances_to_stop,
                         self.reporter.instances_to_stop)

    def test_get_creator_report(self):
        self.reporter.low_use_instances = [
            {
                'Creator': 'test1',
                'InstanceID': 'test_id_1'
            },
            {
                'Creator': 'test2',
                'InstanceID': 'test_id_2'
            }
        ]

        self.reporter.instances_scheduled_for_deletion = [
            {
                'Creator': 'test1',
                'InstanceID': 'test_id_1_delete'
            },
            {
                'Creator': 'test2',
                'InstanceID': 'test_id_2_delete'
            }
        ]

        expected_creator_reports = [
            {
                'creator': 'test1',
                'low_use': [{
                    'Creator': 'test1',
                    'InstanceID': 'test_id_1'
                }],
                'scheduled_for_deletion': [{
                    'Creator': 'test1',
                    'InstanceID': 'test_id_1_delete'
                }]},
            {
                'creator': 'test2',
                'low_use': [{
                    'Creator': 'test2',
                    'InstanceID': 'test_id_2'
                }],
                'scheduled_for_deletion': [{
                    'Creator': 'test2',
                    'InstanceID': 'test_id_2_delete'
                }]}
        ]
        result = list(self.reporter.get_creator_report())
        self.assertCountEqual(expected_creator_reports, result)

    def test_start(self):
        pass
