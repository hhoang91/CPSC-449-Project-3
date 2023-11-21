from typing import Annotated
import boto3
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter
from .db_connection import get_db
from dynamodb_classes.classes import create_class_instance
WAITLIST_CAPACITY = 15
MAX_NUMBER_OF_WAITLISTS_PER_STUDENT = 3

student_router = APIRouter()

@student_router.get("/classes/available/")
def get_available_classes(db: boto3.resource = Depends(get_db)):
    try: 
        class_table_manager = create_class_instance()
        table_name = "class_table"
        class_table_manager.table = class_table_manager.dyn_resource.Table(table_name)

        # Perform a scan to retrieve all items
        response = class_table_manager.table.scan()

        # Extract the items from the response
        items = response.get('Items', [])

        # Print or process the items
        for item in items:
            print(item)

        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving classes: {str(e)}")