import boto3

class EC2EventParser:
    def __init__(self, ec2, event, context):
        self.ec2 = ec2
        self.event = event
        self.context = context
    
    def get_username(self):
        """Get username

        Gets the username of the account that created the instance(s) in question

        Returns:
            str: Username of the account
        """
        return self.event['userIdentity'].get('userName', 'None')

    def get_event_name(self):
        return self.event['detail'].get('eventName', 'None')

    def get_created_instance_ids(self):
        instance_ids = []
        for instance in self.event['detail']['responseElements']['instancesSet'].get('items', []):
            instance_ids.append(instance['instanceId'])
        return instance_ids

    def get_resource_ids(self, event_name):
        response = self.event['detail']['responseElements']
        if event_name == 'CreateImage':
            return [response['imageId']]
        elif event_name == 'RunInstances':
            return self.get_created_instance_ids()
        elif event_name == 'CreateSecurityGroup':
            return [response['groupId']]
        elif event_name == 'CreateVolume':
            return [response['volumeId']]
        else:
            return []

    def parse_event(self):
        return self.get_username(), self.get_resource_ids(self.get_event_name())
        
