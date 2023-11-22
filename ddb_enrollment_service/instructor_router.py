from typing import Annotated
import boto3
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter
from .db_connection import get_db
from ddb_enrollment_schema import *
from boto3.dynamodb.conditions import Key
WAITLIST_CAPACITY = 15
MAX_NUMBER_OF_WAITLISTS_PER_STUDENT = 3

instructor_router = APIRouter()

@instructor_router.get("/classes/{class_id}/students")
def get_current_enrollment(class_id: int,
              db: boto3.resource = Depends(get_db)):
    """
    Retreive current enrollment for the classes.

    Parameters:
    - class_id (int): The ID of the class.

    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        enrollment_table_instance = create_table_instance(Enrollment, "enrollment_table")

        response = enrollment_table_instance.table.query(KeyConditionExpression=Key('class_id').eq(class_id))

        items = response.get('Items', [])

        return {"enrollments" : items}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving enrollments: {str(e)}")