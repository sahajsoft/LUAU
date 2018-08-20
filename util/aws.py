import boto3 
import logging 

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

LOW_USE_CHECK_ID = 'Qch7DwouX1'

class EC2Wrapper:
    def __init__(self, session):
        self.session = session
        self.ec2 = session.client('ec2')
    
    def create_tags(self, Resources, Tags):
        return self.ec2.create_tags(
            Resources=Resources,
            Tags=Tags
        )

class ASGWrapper:
    def __init__(self, session):
        self.session = session
        self.asg = session.client('autoscaling')

    def get_asg_user_tag_by_instance_id(self, instance_ids):
        """Get the name of the ASG for these instances

        This is done to ensure that the owner of the ASG is accurated tagged as the owner
        of the instances belonging to the ASG

        Params:
            instance_ids ([str]): List of instance_ids that belong to the same ASG
        Returns:
            str: The ASG Name associated with these instances
        """
        # Use the first instance because all of them will belong to the same ASG
        instance_id = instance_ids[0]
        instance_data = self.asg.describe_auto_scaling_instances(InstanceIds=[instance_id])
        try:
            return instance_data['AutoScalingInstances'][0]['AutoScalingGroupName']
        except KeyError as e:
            logger.warning('Instance does not exist: %s', str(e))
        except Exception as e:
            logger.error('Unknown Error: %s', str(e))

    def get_asg_instance_ids(self, asg_name): 
        """Get the instance_ids of instances belonging to an ASG

        Params:
            asg_name (str): Name of an ASG
        Returns:
            [str]: List of ids of instances in the ASG 

        """
        instance_ids = []
        # Grab the first item in the list because we're only asking for 1 ASG
        asg_data = self.asg.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name])['AutoScalingGroups'][0]

        for instance_data in asg_data['Instances']:
            instance_ids.append(instance_data['InstanceId'])

        return instance_ids

        

    def create_or_update_tags(self, Tags):
        tag = Tags[0]
        asg_name = tag['ResourceId']
        ec2_tag = {
            'Key': tag['Key'],
            'Value': tag['Value']
        }
        try:
            response = self.asg.create_or_update_tags(
                Tags=Tags
            )
        except Exception as e:
            logger.error('Unknown Error: %s', str(e))
        else: 
            logger.info(response)

        asg_instances = self.get_asg_instance_ids(asg_name)
        EC2Wrapper(self.session).create_tags(Resources=asg_instances, Tags=[ec2_tag])

class TrustedAdvisor:
    def __init__(self, session):
        self.session = session
        self.support = session.client('support')

    def get_low_use_instances(self):
       response = self.support.describe_trusted_advisor_check_result(checkId=LOW_USE_CHECK_ID, language='en')
       if 'result' in response:
           return response['result'].get('flaggedResources', [])
    
    def get_low_use_summary(self):
        response = self.support.describe_trusted_advisor_check_summaries(checkIds=[LOW_USE_CHECK_ID])
        for checks in response.get('summaries', []):
            if checks['checkId'] == LOW_USE_CHECK_ID:
                return checks
        return None
