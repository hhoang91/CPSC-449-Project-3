from typing import Annotated
import boto3
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter
from .db_connection import get_db
from dynamodb_classes.classes import create_class_instance
from dynamodb_classes.enrollment import create_enrollment_instance
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
        enrollment_table_manager = create_enrollment_instance()
        table_name = "enrollment_table"
        enrollment_table_manager.table = enrollment_table_manager.dyn_resource.Table(table_name)

        # Perform a scan to retrieve all items
        response = enrollment_table_manager.table.query(KeyConditionExpression=Key('class_id').eq(class_id))

        # Extract the items from the response
        items = response.get('Items', [])

        # Print or process the items
        for item in items:
            print(item)

        return items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving enrollments: {str(e)}")