from typing import Annotated
import boto3
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter
from .db_connection import get_db
from ddb_enrollment_schema import *
WAITLIST_CAPACITY = 15
MAX_NUMBER_OF_WAITLISTS_PER_STUDENT = 3

student_router = APIRouter()

@student_router.get("/classes/available/")
def get_available_classes(db: boto3.resource = Depends(get_db)):
    try: 
        class_table_instance = create_table_instance(Class, "class_table")

        # Perform a scan to retrieve all items
        response = class_table_instance.scan()

        # Extract the items from the response
        items = response.get('Items', [])

        # Print or process the items
        for item in items:
            print(item)

        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving classes: {str(e)}")