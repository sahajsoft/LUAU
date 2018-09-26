# DynamoWrappers that help access CRUD functionality of dynamoDB


class DynamoWrapper(object):
    """
    Handler for dynamodb data
    """
    def __init__(self, session):
        self.session = session
        self.dynamo = session.resource('dynamodb')
        self.low_use = self.dynamo.Table('LowUse')
        self.whitelist = self.dynamo.Table('Whitelist')

    def get_whitelist_instance(self, instance_id):
        """
        Fetch Instance from whitelist table.
        """
        key = {"InstanceID": instance_id}
        return self.whitelist.get_item(Key=key)

    def get_low_use_instance(self, instance_id):
        """
        Fetch instance from whitelist table
        """
        key = {"InstanceID": instance_id}
        return self.low_use.get_item(Key=key)

    def is_whitelisted(self, instance_id):
        item = self.get_whitelist_instance(instance_id)
        if item is None:
            return False
        else:
            return True

    def is_low_use(self, instance_id):
        item = self.get_low_use_instance(instance_id)
        if item is None:
            return False
        else:
            return True

    def is_scheduled_for_deletion(self, instance_id):
        item = self.get_low_use_instance(instance_id)
        if item is not None:
            return item.get('Scheduled For Deletion', False)

    def add_to_whitelist(self, instance_id, creator, reason):
        item = {
            "InstanceID": instance_id,
            "Creator": creator,
            "Reason": reason,
            "EmailSent": False
        }
        self.delete_from_low_use(instance_id)
        response = self.whitelist.put_item(Item=item)
        return response

    def add_to_low_use(self, instance_id, creator):
        item = {
            "InstanceID": instance_id,
            "Creator": creator,
            "Scheduled For Deletion": False,
            "EmailSent": False
        }

        return self.low_use.put_item(Item=item)

    def schedule_for_deletion(self, instance_id, creator):
        item = {
            "InstanceID": instance_id,
            "Creator": creator,
            "Scheduled For Deletion": True
        }

        return self.low_use.put_item(Item=item)

    def delete_from_low_use(self, instance_id):
        key = {"InstanceID": instance_id}
        return self.low_use.delete_item(Key=key)

    def batch_delete_item_from_low_use(self, instance_ids): 
        for instance_id in instance_ids:
            self.delete_from_low_use(instance_id)


class EmailDynamoWrapper(DynamoWrapper):
    """
    Extending the DynamoWrapper to handle email queries

    We want to get instances where EmailSet is set to False for
    Lowuse table and whitelisted table
    """

    def __init__(self, session):
        super(EmailDynamoWrapper).__init__(session)
        self.type_map = {"low_use": self.low_use,
                         "whitelist": self.whitelist}

    def get_low_use_instances(self):
        """
        Fetch instance from whitelist table
        """
        return self.low_use.batch_get_item(EmailSent=True)

    def get_whitelist_instances(self):
        """
        Fetch Instance from whitelist table.
        """
        return self.whitelist.batch_get_item(EmailSent=True)

    def set_email_sent(self, instance_id, creator, type):
        """
        Set EmailSent key value to True after email is sent.
        """
        table = self.type_map[type]
        item = {
                "InstanceID": instance_id,
                "Creator": creator,
                "Scheduled For Deletion": True,
                "EmailSent": True
                }
        return table.put_item(item)
