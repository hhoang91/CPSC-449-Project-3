from typing import Annotated
import boto3
from fastapi import Depends, Response, HTTPException, Body, status, APIRouter
from .db_connection import get_db
from ddb_enrollment_schema import *
from boto3.dynamodb.conditions import Key
from .models import Course, ClassCreate, ClassPatch
WAITLIST_CAPACITY = 15
MAX_NUMBER_OF_WAITLISTS_PER_STUDENT = 3

registrar_router = APIRouter()

@registrar_router.post("/classes/", status_code=status.HTTP_201_CREATED)
def create_class(
    body_data: ClassCreate, response: Response
):
    """
    Creates a new class.

    Parameters:
    - `class` (Class): The JSON object representing the class with the following properties:
        - `dept_code` (str): Department code.
        - `course_num` (int): Course number.
        - `section_no` (int): Section number.
        - `academic_year` (int): Academic year.
        - `semester` (str): Semester name (SP, SU, FA, WI).
        - `instructor_id` (int): Instructor ID.
        - `room_num` (int): Room number.
        - `room_capacity` (int): Room capacity.
        - `course_start_date` (str): Course start date (format: "YYYY-MM-DD").
        - `enrollment_start` (str): Enrollment start date (format: "YYYY-MM-DD HH:MM:SS.SSS").
        - `enrollment_end` (str): Enrollment end date (format: "YYYY-MM-DD HH:MM:SS.SSS").

    Returns:
    - dict: A dictionary containing the details of the created item.

    Raises:
    - HTTPException (409): If a conflict occurs (e.g., duplicate course).
    """
    try:
        class_table_instance = create_table_instance(Class, "class_table")

        item_to_add = {
            "id": body_data.id,
            "dept_code": body_data.dept_code,
            "course_num": body_data.course_num,
            "section_no": body_data.section_no,
            "academic_year": body_data.academic_year,
            "semester": body_data.semester,
            "instructor_id": body_data.instructor_id,
            "room_num": body_data.room_num,
            "room_capacity": body_data.room_capacity,
            "course_start_date": body_data.course_start_date,
            "enrollment_start": body_data.enrollment_start,
            "enrollment_end": body_data.enrollment_end,
        }

        class_table_instance.put_item(Item=item_to_add)

        return item_to_add

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating class: {str(e)}")

