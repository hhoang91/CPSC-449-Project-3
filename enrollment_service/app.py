from typing import Annotated
import sqlite3
import contextlib
from fastapi import FastAPI, Depends, Response, HTTPException, Header, Body, status
from .enrollment_helper import enroll_students_from_waitlist, is_auto_enroll_enabled, get_opening_sections
from .models import Settings, Course, SectionCreate, SectionPatch, Student, Enrollment, Instructor

settings = Settings()
app = FastAPI()

WAITLIST_CAPACITY = 15


def get_db():
    with contextlib.closing(sqlite3.connect(settings.database)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        yield db

############### ENDPOINTS FOR REGISTRAS ################


@app.put("/auto-enrollment/")
def set_auto_enrollment(enabled: Annotated[bool, Body(embed=True)], db: sqlite3.Connection = Depends(get_db)):
    try:
        flag = 1 if enabled else 0
        db.execute("UPDATE configs set automatic_enrollment = ?;", [flag])
        db.commit()

        if enabled:
            opening_sections = get_opening_sections(db)
            enroll_students_from_waitlist(db, opening_sections)

    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"detail ": f"Auto enrollment: {enabled}"}


@app.post("/courses/", status_code=status.HTTP_201_CREATED)
def create_course(
    course: Course, response: Response, db: sqlite3.Connection = Depends(get_db)
):
    """
    Creates a new course with the provided details.

    Parameters:
    - `course` (CourseInput): JSON body input for the course with the following fields:
        - `department_code` (str): The department code for the course.
        - `course_no` (int): The course number.
        - `title` (str): The title of the course.

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
            """, record)
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
    Creates a new section.

    Parameters:
    - `section` (Section): The JSON object representing the section with the following properties:
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
            INSERT INTO section(dept_code, course_num, section_no, 
                    academic_year, semester, instructor_id, room_num, room_capacity, 
                    course_start_date, enrollment_start, enrollment_end)
            VALUES(:dept_code, :course_num, :section_no,
                    :academic_year, :semester, :instructor_id, :room_num, :room_capacity, 
                    :course_start_date, :enrollment_start, :enrollment_end)
            """, record)
        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    response.headers["Location"] = f"/sections/{cur.lastrowid}"
    return {"detail": "Success", "inserted_id": cur.lastrowid}


@app.delete("/sections/{id}", status_code=status.HTTP_200_OK)
def delete_section(
    id: int, response: Response, db: sqlite3.Connection = Depends(get_db)
):
    """
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
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )
        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"detail": "Item deleted successfully"}


@app.patch("/sections/{id}", status_code=status.HTTP_200_OK)
def update_section(
    id: int,
    section: SectionPatch,
    response: Response,
    db: sqlite3.Connection = Depends(get_db),
):
    """
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
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )
        db.commit()
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    return {"message": "Section updated successfully"}

############### ENDPOINTS FOR STUDENTS ################


@app.get("/classes/available/")
def get_available_classes(db: sqlite3.Connection = Depends(get_db)):
    """
    Retreive all available classes.

    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        classes = db.execute(
            """
            SELECT s.*
            FROM "section" as s
            WHERE datetime('now') BETWEEN s.enrollment_start AND s.enrollment_end 
                AND (
                        (s.room_capacity > 
                            (SELECT COUNT(enrollment.student_id)
                            FROM enrollment
                            WHERE section_id=s.id) > 0) 
                        OR ((SELECT COUNT(waitlist.student_id)
                            FROM waitlist
                            WHERE section_id=s.id) < ?)
                    );
            """, [WAITLIST_CAPACITY]
        )
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    finally:
        return {"classes": classes.fetchall()}


@app.post("/enroll/")
def enroll(section_id: Annotated[int, Body(embed=True)],
           student_id: int = Header(
               alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
           first_name: str = Header(alias="x-first-name"),
           last_name: str = Header(alias="x-last-name"),
           db: sqlite3.Connection = Depends(get_db)):
    """
    Student enrolls in a section

    Parameters:
    - section_id (int, in the request body): The unique identifier of the section where students will be enrolled.
    - student_id (int, in the request header): The unique identifier of the student who is enrolling.

    Returns:
    - HTTP_200_OK on success

    Raises:
    - HTTPException (400): If there are no available seats.
    - HTTPException (404): If the specified section or student does not exist.
    - HTTPException (409): If a conflict occurs (e.g., The student has already enrolled into the class).
    - HTTPException (500): If there is an internal server error.
    """

    try:
        section = db.execute(
            """
            SELECT course_start_date, enrollment_start, enrollment_end, datetime('now') AS datetime_now, 
                    (room_capacity - COUNT(enrollment.section_id)) AS available_seats
            FROM section LEFT JOIN enrollment ON section.id = enrollment.section_id 
            WHERE section.id = ?;
            """, [section_id]).fetchone()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Section Not Found")

        if not (section["enrollment_start"] <= section["datetime_now"] <= section["enrollment_end"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Not Available At The Moment")

        # Insert student if not exists
        db.execute(
            """
            INSERT OR IGNORE INTO student (id, first_name, last_name)
            VALUES (?, ?, ?);
            """, [student_id, first_name, last_name])

        if section["available_seats"] <= 0:
            # ----- INSERT INTO WAITLIST TABLE -----
            result = db.execute(
                """
                SELECT COUNT(student_id) 
                FROM waitlist 
                WHERE section_id = ?
                """, section_id).fetchone()

            if int(result[0]) >= WAITLIST_CAPACITY:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="No open seats and the waitlist is also full")
            else:
                db.execute(
                    """
                    INSERT INTO waitlist(section_id, student_id, waitlist_date) 
                    VALUES(?, ?, datetime('now'))
                    """, [section_id, student_id]
                )
        else:
            # ----- INSERT INTO ENROLLMENT TABLE -----
            db.execute(
                """
                INSERT INTO enrollment(section_id, student_id, enrollment_date) 
                VALUES(?, ?, datetime('now'))
                """, [section_id, student_id]
            )

        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="The student has already enrolled into the class")

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))

    return {"detail": "success"}


@app.delete("/enrollment/{section_id}", status_code=status.HTTP_200_OK)
def drop_class(
    section_id: int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        curr = db.execute(
            "DELETE FROM enrollment WHERE section_id=? AND student_id=?", [section_id, student_id])

        if curr.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )
        
        db.execute(
            """
            INSERT INTO droplist (section_id, student_id, drop_date, administrative) 
            VALUES (?, ?, datetime('now'), 0);
            """, [section_id, student_id]
        )

        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"detail": "Item deleted successfully"}

@app.get("/sections/{section_id}/waitlistposition/")
def get_current_waitlist_position(
    section_id:int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: sqlite3.Connection = Depends(get_db)):
    """
    Retreive all available classes.

    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        result = db.execute(
            """
            SELECT COUNT(student_id)
            FROM waitlist
            WHERE section_id=? AND 
                waitlist_date <= (SELECT waitlist_date 
                                    FROM waitlist
                                    WHERE section_id=? AND 
                                            student_id=?)
            ;
            """, [section_id, section_id, student_id]
        )
        return {"position": result.fetchone()[0]}
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
        


############### ENDPOINTS FOR INSTRUCTORS ################

@app.get("/classes/{section_id}/students")
def get_class(section_id: int,
              instructor_id: int = Header(
                  alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
              db: sqlite3.Connection = Depends(get_db)):
    """
    Retreive current enrollment for the classes.

    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        result = db.execute(
            """
            SELECT stu.* 
            FROM section sec
                INNER JOIN enrollment e ON sec.id = e.section_id
                INNER JOIN student stu ON e.student_id = stu.id 
            WHERE sec.id=? AND sec.instructor_id=?
            """, [section_id, instructor_id]
        )
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    finally:
        return {"students": result.fetchall()}

@app.get("/classes/{section_id}/droplist")
def get_class(section_id: int,
              instructor_id: int = Header(
                  alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
              db: sqlite3.Connection = Depends(get_db)):
    """
    Retreive students who have dropped the class.

    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        result = db.execute(
            """
            SELECT stu.* 
            FROM section sec
                INNER JOIN droplist d ON sec.id = d.section_id
                INNER JOIN student stu ON d.student_id = stu.id 
            WHERE sec.id=? AND sec.instructor_id=?
            """, [section_id, instructor_id]
        )
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    finally:
        return {"students": result.fetchall()}

@app.delete("/enrollment/{section_id}/{student_id}/administratively/", status_code=status.HTTP_200_OK)
def drop_class(
    section_id: int,
    student_id: int,
    instructor_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        curr = db.execute(
            """
            DELETE 
            FROM enrollment
            WHERE section_id = ? AND student_id=? 
                AND section_id IN (SELECT id 
                                    FROM "section" 
                                    WHERE id=? AND instructor_id=?);
            """, [section_id, student_id, section_id, instructor_id])

        if curr.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )
        
        db.execute(
            """
            INSERT INTO droplist (section_id, student_id, drop_date, administrative) 
            VALUES (?, ?, datetime('now'), 1);
            """, [section_id, student_id]
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"detail": "Item deleted successfully"}