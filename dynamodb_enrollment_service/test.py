import boto3
from dynamodb_classes.classes import create_class_instance
from dynamodb_classes.enrollment import create_enrollment_instance
from boto3.dynamodb.conditions import Key


enrollment_table_manager = create_enrollment_instance()
table_name = "enrollment_table"
enrollment_table_manager.table = enrollment_table_manager.dyn_resource.Table(table_name)

# Perform a scan to retrieve all items
response = enrollment_table_manager.table.query(KeyConditionExpression=Key('class_id').eq(1))

# Extract the items from the response
items = response.get('Items', [])

# Print or process the items
for item in items:
    print(item)

# class_table_manager = create_class_instance()
# table_name = "class_table"
# class_table_manager.table = class_table_manager.dyn_resource.Table(table_name)

# # Perform a scan to retrieve all items
# response = class_table_manager.table.scan()

# # Extract the items from the response
# items = response.get('Items', [])

# # Print or process the items
# for item in items:
#     print(item)
