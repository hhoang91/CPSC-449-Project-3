from typing import Annotated
import boto3
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter
from .db_connection import get_db
from ddb_enrollment_schema import *
from boto3.dynamodb.conditions import Key
from datetime import datetime
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
