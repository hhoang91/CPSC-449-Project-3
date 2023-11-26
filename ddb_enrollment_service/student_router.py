from typing import Annotated
import boto3
import botocore
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter
from .db_connection import get_db
from ddb_enrollment_schema import *
from boto3.dynamodb.conditions import Key
from datetime import datetime
import redis
#from .ddb_enrollment_helper import enroll_students_from_waitlist, is_auto_enroll_enabled
from .ddb_enrollment_helper import DynamoDBRedisHelper

# Assuming you have DynamoDB resource and Redis connection instances available
# Replace these with your actual instances
dynamodb_resource = boto3.resource('dynamodb', region_name='local')
redis_conn = redis.Redis(decode_responses=True)
ddb_helper_instance = DynamoDBRedisHelper(dynamodb_resource, redis_conn)

# Instantiate the Class class
class_table_manager = Class(dynamodb_resource)

WAITLIST_CAPACITY = 15
MAX_NUMBER_OF_WAITLISTS_PER_STUDENT = 3

student_router = APIRouter()

# Create an instance of DynamoDBRedisHelper
#ddb_helper_instance = DynamoDBRedisHelper()

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

        return {"available_classes" : available_classes}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving classes: {str(e)}")
    
@student_router.post("/enrollment/")
def enroll(class_id: Annotated[int, Body(embed=True)],
           student_id: int = Header(
               alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
           first_name: str = Header(alias="x-first-name"),
           last_name: str = Header(alias="x-last-name")):
    """
    Student enrolls in a class

    Parameters:
    - class_id (int, in the request body): The unique identifier of the class where students will be enrolled.
    - student_id (int, in the request header): The unique identifier of the student who is enrolling.

    Returns:
    - HTTP_200_OK on success

    Raises:
    - HTTPException (400): If there are no available seats.
    - HTTPException (404): If the specified class does not exist.
    - HTTPException (409): If a conflict occurs (e.g., The student has already enrolled into the class).
    - HTTPException (500): If there is an internal server error.
    """

    try:
        class_table_instance = create_table_instance(Class, "class_table")
        enrollment_table_instance = create_table_instance(Enrollment, "enrollment_table")

        response = class_table_instance.query(KeyConditionExpression=Key('id').eq(class_id))
        class_item = response.get('Items', [])[0]
        room_capacity = class_item['room_capacity']
        enrollments = enrollment_table_instance.query(KeyConditionExpression=Key('class_id').eq(class_id))

        num_of_enrollments = len(enrollments.get('Items', []))
        if num_of_enrollments < room_capacity:
            enrollment_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            item_to_add = {
                "class_id": class_id,
                "enrollment_date": enrollment_date,
                "student_id" : student_id
            }

            enrollment_table_instance.put_item(Item=item_to_add)
            return {"message": "Enrollment successful"}
        else:
             raise HTTPException(status_code=400, detail="No available seats in the class.")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving classes: {str(e)}")


@student_router.delete("/enrollment/{class_id}", status_code=status.HTTP_200_OK)
def drop_class(
    class_id: int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: boto3.resource = Depends(get_db)
):
    """
    Handles a DELETE request to drop a student (himself/herself) from a specific class.

    Parameters:
    - class_id (int): The ID of the class from which the student wants to drop.
    - student_id (int, in the header): A unique ID for students, instructors, and registrars.

    Returns:
    - dict: A dictionary with the detail message indicating the success of the operation.

    Raises:
    - HTTPException (404): If the specified enrollment record is not found.
    - HTTPException (409): If a conflict occurs.
    """
    try:
        enrollment_table_instance = create_table_instance(Enrollment, "enrollment_table")

        # Check if the enrollment record exists
        enrollment_response = enrollment_table_instance.query(
            KeyConditionExpression=Key('class_id').eq(class_id) & Key('student_id').eq(str(student_id))
        )
        enrollment_items = enrollment_response.get('Items', [])

        if not enrollment_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )

        # Delete the enrollment record
        enrollment_table_instance.delete_item(
            Key={
                'class_id': class_id,
                'student_id': str(student_id)
            }
        )

        # Insert into Droplist
        droplist_table_instance = create_table_instance(Droplist, "drolist_table")
        droplist_table_instance.put_item(
            Item={
                "class_id": class_id,
                "student_id": str(student_id),
                "drop_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "administrative": False
            }
        )

        # Trigger auto enrollment using the instance
        if ddb_helper_instance.is_auto_enroll_enabled(db):        
            ddb_helper_instance.enroll_students_from_waitlist(db, [class_id])

    except botocore.exceptions.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"detail": "Item deleted successfully"}


@student_router.get("/waitlist/{class_id}/position/")
def get_current_waitlist_position(
    class_id:int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars")):
    """
    Retreive waitlist position

    Returns:
    - dict: A dictionary containing the user's waitlist position info

    Raises:

    """
    try:
        redis_conn = redis.Redis(decode_responses=True)
        waitlist_key_to_check = f"waitlist_{class_id}"

        waitlist_position = redis_conn.zrank(waitlist_key_to_check, f"{class_id}_{student_id}")

        if waitlist_position is not None:
            waitlist_position += 1
            return {"class_id": class_id, "waitlist_position": waitlist_position}
        else:
            message = f"You are not in the waitlist for class {class_id}"
            return {"class_id": class_id, "message": message}

    except redis.exceptions.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving waitlist position: {str(e)}")
    
@student_router.delete("/waitlist/{class_id}/", status_code=status.HTTP_200_OK)
def remove_from_waitlist(
    class_id: int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"
    )
):
    # Remove student from Redis waitlist
    waitlist_key = f"waitlist_{class_id}"
    member = f"{class_id}_{student_id}"

    if not redis_conn.zrem(waitlist_key, member):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found in Redis"
        )

    return {"detail": "Item deleted successfully"}
     
