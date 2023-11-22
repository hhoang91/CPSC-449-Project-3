from typing import Annotated
import boto3
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter
from .db_connection import get_db
from ddb_enrollment_schema import *
from boto3.dynamodb.conditions import Key
WAITLIST_CAPACITY = 15
MAX_NUMBER_OF_WAITLISTS_PER_STUDENT = 3

student_router = APIRouter()

@student_router.get("/classes/available/")
def get_available_classes(db: boto3.resource = Depends(get_db)):
    try: 
        available_classes = []

        class_table_instance = create_table_instance(Class, "class_table")
        enrollment_table_instance = create_table_instance(Enrollment, "enrollment_table")

        response = class_table_instance.scan()

        items = response.get('Items', [])

        for item in items:
            class_id = item['id']
            room_capacity = item['room_capacity']
            enrollments = enrollment_table_instance.query(KeyConditionExpression=Key('class_id').eq(class_id))
            num_of_enrollments = len(enrollments.get('Items', []))
            if num_of_enrollments < room_capacity:
                available_classes.append(item)

        for item in available_classes:
            print(item)

        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving classes: {str(e)}")