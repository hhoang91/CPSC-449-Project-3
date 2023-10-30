import sqlite3
import contextlib
from fastapi import  FastAPI, Depends, Response, HTTPException, status
from .enrollment_helper import enroll_students_from_waitlist, is_auto_enroll_enabled, get_opening_sections
from .models import Settings, Course, SectionCreate, SectionPatch, Student, Enrollment, Instructor

settings = Settings()
app = FastAPI()

def get_db():
    with contextlib.closing(sqlite3.connect(settings.database)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        yield db

@app.post("/courses/", status_code=status.HTTP_201_CREATED)
def create_course(
    course: Course, response: Response, db: sqlite3.Connection = Depends(get_db)
):
    """
    Create course

    Creates a new course with the provided details.

    Parameters:
    - `course` (CourseInput): JSON body input for the course with the following fields:
        - `department_code` (str): The department code for the course.
        - `course_no` (int): The course number.
        - `title` (str): The title of the course.
        - `description` (str): A description of the course.

    Returns:
    - dict: A dictionary containing the details of the created item.

    Raises:
    - HTTPException (409): If a conflict occurs (e.g., duplicate course).
    """
    record = dict(course)
    try:
        cur = db.execute(
            """
            INSERT INTO course(department_code, course_no, title)
            VALUES(:department_code, :course_no, :title)
            """,
            record,
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    return record


@app.post("/sections/", status_code=status.HTTP_201_CREATED)
def create_section(
    section: SectionCreate, response: Response, db: sqlite3.Connection = Depends(get_db)
):
    """
    Create Section

    Creates a new section.

    Parameters:
    - `section` (Section): The JSON object representing the section with the following properties:
        - `id` (int): The section ID.
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
    record = dict(section)
    try:
        cur = db.execute(
            """
            INSERT INTO section(id, dept_code, course_num, section_no, 
                    semester, year, instructor_id, room_num, room_capacity, 
                    course_start_date, enrollment_start, enrollment_end)
            VALUES(:id, :dept_code, :course_num, :section_no,
                    :semester, :year, :instructor_id, :room_num, :room_capacity, 
                    :course_start_date, :enrollment_start, :enrollment_end)
            """,
            record,
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    record["id"] = cur.lastrowid
    response.headers["Location"] = f"/sections/{record['id']}"
    return record


@app.delete("/sections/{id}", status_code=status.HTTP_200_OK)
def delete_section(
    id: int, response: Response, db: sqlite3.Connection = Depends(get_db)
):
    """
    Delete section

    Deletes a specific section.

    Parameters:
    - `id` (int): The ID of the section to delete.

    Returns:
    - dict: A dictionary indicating the success of the deletion operation.
      Example: {"message": "Item deleted successfully"}

    Raises:
    - HTTPException (404): If the section with the specified ID is not found.
    - HTTPException (409): If there is a conflict in the delete operation.
    """
    try:
        curr = db.execute("DELETE FROM section WHERE id=?;", [id])

        if curr.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record not Found"
            )
        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"message": "Item deleted successfully"}


@app.patch("/sections/{id}", status_code=status.HTTP_200_OK)
def update_section(
    id: int,
    section: SectionPatch,
    response: Response,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Patch Section

    Updates specific details of a section.

    Parameters:
    - `section` (Section): The JSON object representing the section with the following properties:
        - `section_no` (int, optional): Section number.
        - `instructor_id` (int, optional): Instructor ID.
        - `room_num` (int, optional): Room number.
        - `room_capacity` (int, optional): Room capacity.
        - `course_start_date` (str, optional): Course start date (format: "YYYY-MM-DD").
        - `enrollment_start` (str, optional): Enrollment start date (format: "YYYY-MM-DD HH:MM:SS.SSS").
        - `enrollment_end` (str, optional): Enrollment end date (format: "YYYY-MM-DD HH:MM:SS.SSS").

    Returns:
    - dict: A dictionary indicating the success of the update operation.
      Example: {"message": "Section updated successfully"}

    Raises:
    - HTTPException (404): If the section with the specified ID is not found.
    - HTTPException (409): If there is a conflict in the update operation (e.g., duplicate section details).
    """
    try:
        # Excluding fields that have not been set
        section_fields = section.dict(exclude_unset=True)

        # Create a list of column-placeholder pairs, separated by commas
        keys = ", ".join(
            [f"{key} = ?" for index, key in enumerate(section_fields.keys())]
        )

        # Create a list of values to bind to the placeholders
        values = list(section_fields.values())  # List of values to be updated
        values.append(id)  # WHERE id = ?

        # Define a parameterized query with placeholders & values
        update_query = f"UPDATE section SET {keys} WHERE id = ?"

        # Execute the query
        curr = db.execute(update_query, values)

        # Raise exeption if Record not Found
        if curr.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record not Found"
            )
        db.commit()
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    return {"message": "Section updated successfully"}