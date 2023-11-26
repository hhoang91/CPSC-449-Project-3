import boto3
import redis
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from boto3.dynamodb.conditions import Key

# Create Boto3 DynamoDB resource
dynamodb_resource = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:5300'
)

# Create Redis connection
redis_conn = redis.Redis(decode_responses=True)

class DynamoDBRedisHelper:
    def __init__(self, dynamodb_resource, redis_conn):
        self.dynamodb_resource = dynamodb_resource
        self.redis_conn = redis_conn

    def is_auto_enroll_enabled(self):
        configs_table = self.dynamodb_resource.Table("configs_table")
        response = configs_table.get_item(Key={"variable_name": "automatic_enrollment"})

        if "Item" in response:
            return response["Item"]["value"] == "1"
        else:
            return False

    def get_available_classes_within_first_2weeks(self):
        class_table = self.dynamodb_resource.Table("class_table")
        two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()

        response = class_table.query(
            IndexName='course_start_date_index',
            KeyConditionExpression=Key('course_start_date').gte(two_weeks_ago) & Key('enrollment_count').lt('room_capacity'),
            ProjectionExpression='id'
        )

        return [item["id"] for item in response.get("Items", [])]

    def enroll_students_from_waitlist(self, class_id_list):
        enrollment_count = 0

        for class_id in class_id_list:
            enrollment_table = self.dynamodb_resource.Table("enrollment_table")
            waitlist_key = f"waitlist_{class_id}"
            waitlist_members = self.redis_conn.zrange(waitlist_key, 0, -1)

            class_table = self.dynamodb_resource.Table("class_table")
            class_info = class_table.get_item(Key={"id": class_id}).get("Item", {})
            available_spots = class_info.get("room_capacity", 0) - class_info.get("enrollment_count", 0)

            for waitlist_member in waitlist_members[:available_spots]:
                student_id = waitlist_member.split("_")[1]

                enrollment_table.put_item(
                    Item={"class_id": class_id, "student_id": student_id, "enrollment_date": datetime.now().isoformat()}
                )

                self.redis_conn.zrem(waitlist_key, waitlist_member)

                enrollment_count += 1

        return enrollment_count

# Instantiate DynamoDBRedisHelper
helper = DynamoDBRedisHelper(dynamodb_resource, redis_conn)

# Example usage
if helper.is_auto_enroll_enabled():
    available_classes = helper.get_available_classes_within_first_2weeks()
    enrollment_count = helper.enroll_students_from_waitlist(available_classes)
    print(f"Enrolled {enrollment_count} students from the waitlist.")
