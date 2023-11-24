import boto3
from ddb_enrollment_schema import *


class_table_instance = create_table_instance(Class, "class_table")
items_to_insert = [
    {
        "id": "1",
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
        "class_id": "1",
        "student_id" : "1"
    },
]
for item in items_to_insert:
    enrollment_table_instance.put_item(Item=item)

#####################################################################################################################
droplist_table_instance = create_table_instance(Droplist, "droplist_table")
items_to_insert = [
    {
        "class_id": "1",
        "student_id" : "1",
        "drop_date": "2023-06-01 09:00:00",
        "administrative" : True
    },
    {
        "class_id": "1",
        "student_id" : "2",
        "drop_date": "2023-06-01 09:00:00",
        "administrative" : False
    }
]
for item in items_to_insert:
    droplist_table_instance.put_item(Item=item)

#####################################################################################################################
configs_table_instance = create_table_instance(Configs, "configs_table")
items_to_insert = [
    {
        "variable_name": "automatic_enrollment",
        "value": True
    },
]
for item in items_to_insert:
    configs_table_instance.put_item(Item=item)

#####################################################################################################################
department_table_instance = create_table_instance(Department, "department_table")
items_to_insert = [
    {
        "code": "CPSC",
        "department_name": "Computer science"
    },
]
for item in items_to_insert:
    department_table_instance.put_item(Item=item) 

#####################################################################################################################
course_table_instance = create_table_instance(Course, "course_table")
items_to_insert = [
    {
        "department_code": "CPSC",
        "course_no": 449,
        "course_name": "Backend-Engineering"
    },
]
for item in items_to_insert:
    course_table_instance.put_item(Item=item)     

#####################################################################################################################
instructor_table_instance = create_table_instance(Instructor, "instructor_table")
items_to_insert = [
    {
        "id": "1",
        "first_name": "Keynett",
        "last_name": "Avery"
    },
]
for item in items_to_insert:
    instructor_table_instance.put_item(Item=item)

#####################################################################################################################
student_table_instance = create_table_instance(Student, "student_table")
items_to_insert = [
    {
        "id": "1",
        "first_name": "John",
        "last_name": "Doe"
    },
]
for item in items_to_insert:
    student_table_instance.put_item(Item=item)                             