import boto3
from ddb_enrollment_service.ddb_enrollment_schema import *


class_table_instance = create_table_instance(Class, "class_table")
items_to_insert = [
    {
        "id": 1,
        "dept_code": "CPSC",
        "course_num": 101,
        "section_no": 1,
        "academic_year": 2023,
        "semester": "SU",
        "instructor_id": 1,
        "room_num": 101,
        "room_capacity": 30,
        "course_start_date": "2023-06-12",
        "enrollment_start": "2023-06-01 09:00:00",
        "enrollment_end": "2023-06-15 17:00:00",
    },
]
for item in items_to_insert:
    class_table_instance.put_item(Item=item)
#####################################################################################################################
enrollment_table_instance = create_table_instance(Enrollment, "enrollment_table")
items_to_insert = [
    {
        "class_id": 1,
        "enrollment_date": "CPSC",
        "student_id" : 1
    },
]
for item in items_to_insert:
    enrollment_table_instance.put_item(Item=item)