import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class Class:
    """Encapsulates an Amazon DynamoDB table for configurations."""

    def __init__(self, dyn_resource):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.table = None

    def create_table(self, table_name):
        """
        Creates an Amazon DynamoDB table for configurations.

        :param table_name: The name of the table to create.
        :return: The newly created table.
        """
        try:
            # Check if the table already exists
            existing_tables = [table.name for table in self.dyn_resource.tables.all()]
            if table_name in existing_tables:
                print(f"Table {table_name} already exists. Deleting the existing table.")
                existing_table = self.dyn_resource.Table(table_name)
                existing_table.delete()
                existing_table.wait_until_not_exists()

            # Create the new table
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "N"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            )
            self.table.wait_until_exists()
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return self.table

class Enrollment:
    """Encapsulates an Amazon DynamoDB table for configurations."""

    def __init__(self, dyn_resource):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.table = None

    def create_table(self, table_name):
        """
        Creates an Amazon DynamoDB table for configurations.

        :param table_name: The name of the table to create.
        :return: The newly created table.
        """
        try:
            # Check if the table already exists
            existing_tables = [table.name for table in self.dyn_resource.tables.all()]
            if table_name in existing_tables:
                print(f"Table {table_name} already exists. Deleting the existing table.")
                existing_table = self.dyn_resource.Table(table_name)
                existing_table.delete()
                existing_table.wait_until_not_exists()
                
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "class_id", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "student_id", "KeyType": "RANGE"} # Sort Key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "class_id", "AttributeType": "N"},
                    {"AttributeName": "student_id", "AttributeType": "N"}
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            )
            self.table.wait_until_exists()
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return self.table

def create_table_instance(class_type, table_name):
    dynamodb_resource = boto3.resource(
        'dynamodb',
        aws_access_key_id='fakeMyKeyId',
        aws_secret_access_key='fakeSecretAccessKey',
        endpoint_url='http://localhost:5300'
    )
    table_manager = class_type(dynamodb_resource)
    table_manager.table = table_manager.dyn_resource.Table(table_name)
    return table_manager.table

def create_table(class_type, table_name):
    dynamodb_resource = boto3.resource(
        'dynamodb',
        aws_access_key_id='fakeMyKeyId',
        aws_secret_access_key='fakeSecretAccessKey',
        endpoint_url='http://localhost:5300'
    )
    table_manager = class_type(dynamodb_resource)
    table_manager.create_table(table_name)
    print(f"Table {table_name} created successfully.")

if __name__ == "__main__":
    create_table(Class, "class_table")
    create_table(Enrollment, "enrollment_table")