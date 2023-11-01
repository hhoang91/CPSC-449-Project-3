from typing import Annotated
import sqlite3
import contextlib
from fastapi import FastAPI, Depends, Response, HTTPException, Header, Body, status
from .enrollment_helper import enroll_students_from_waitlist, is_auto_enroll_enabled, get_opening_classes
from .models import Settings, Course, ClassCreate, ClassPatch, Student, Enrollment, Instructor

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
    """
    Endpoint for enabling/disabling automatic enrollment.

    Parameters:
    - enabled (bool): A boolean indicating whether automatic enrollment should be enabled or disabled.

    Raises:
    - HTTPException (409): If there is an integrity error while updating the database.

    Returns:
        dict: A dictionary containing a detail message confirming the status of auto enrollment.
    """
    try:
        db.execute("UPDATE configs set automatic_enrollment = ?;", [enabled])
        db.commit()

        if enabled:
            opening_classes = get_opening_classes(db)
            enroll_students_from_waitlist(db, opening_classes)

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

@app.post("/classes/", status_code=status.HTTP_201_CREATED)
def create_class(
    body_data: ClassCreate, response: Response, db: sqlite3.Connection = Depends(get_db)
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
    record = dict(body_data)
    try:
        cur = db.execute(
            """
            INSERT INTO class(dept_code, course_num, section_no, 
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
    response.headers["Location"] = f"/classes/{cur.lastrowid}"
    return {"detail": "Success", "inserted_id": cur.lastrowid}

@app.delete("/classes/{id}", status_code=status.HTTP_200_OK)
def delete_class(
    id: int, response: Response, db: sqlite3.Connection = Depends(get_db)
):
    """
    Deletes a specific class.

    Parameters:
    - `id` (int): The ID of the class to delete.

    Returns:
    - dict: A dictionary indicating the success of the deletion operation.
      Example: {"message": "Item deleted successfully"}

    Raises:
    - HTTPException (404): If the class with the specified ID is not found.
    - HTTPException (409): If there is a conflict in the delete operation.
    """
    try:
        curr = db.execute("DELETE FROM class WHERE id=?;", [id])

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

@app.patch("/classes/{id}", status_code=status.HTTP_200_OK)
def update_class(
    id: int,
    body_data: ClassPatch,
    response: Response,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Updates specific details of a class.

    Parameters:
    - `class` (ClassPatch): The JSON object representing the class with the following properties:
        - `section_no` (int, optional): Section number.
        - `instructor_id` (int, optional): Instructor ID.
        - `room_num` (int, optional): Room number.
        - `room_capacity` (int, optional): Room capacity.
        - `course_start_date` (str, optional): Course start date (format: "YYYY-MM-DD").
        - `enrollment_start` (str, optional): Enrollment start date (format: "YYYY-MM-DD HH:MM:SS.SSS").
        - `enrollment_end` (str, optional): Enrollment end date (format: "YYYY-MM-DD HH:MM:SS.SSS").

    Returns:
    - dict: A dictionary indicating the success of the update operation.
      Example: {"message": "Item updated successfully"}

    Raises:
    - HTTPException (404): If the class with the specified ID is not found.
    - HTTPException (409): If there is a conflict in the update operation (e.g., duplicate class details).
    """
    try:
        # Excluding fields that have not been set
        data_fields = body_data.dict(exclude_unset=True)

        # Create a list of column-placeholder pairs, separated by commas
        keys = ", ".join(
            [f"{key} = ?" for index, key in enumerate(data_fields.keys())]
        )

        # Create a list of values to bind to the placeholders
        values = list(data_fields.values())  # List of values to be updated
        values.append(id)  # WHERE id = ?

        # Define a parameterized query with placeholders & values
        update_query = f"UPDATE class SET {keys} WHERE id = ?"

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
    return {"message": "Item updated successfully"}

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
            FROM "class" as s
            WHERE datetime('now') BETWEEN s.enrollment_start AND s.enrollment_end 
                AND (
                        (s.room_capacity > 
                            (SELECT COUNT(enrollment.student_id)
                            FROM enrollment
                            WHERE class_id=s.id) > 0) 
                        OR ((SELECT COUNT(waitlist.student_id)
                            FROM waitlist
                            WHERE class_id=s.id) < ?)
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

@app.post("/enrollment/")
def enroll(class_id: Annotated[int, Body(embed=True)],
           student_id: int = Header(
               alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
           first_name: str = Header(alias="x-first-name"),
           last_name: str = Header(alias="x-last-name"),
           db: sqlite3.Connection = Depends(get_db)):
    """
    Student enrolls in a class

    Parameters:
    - class_id (int, in the request body): The unique identifier of the class where students will be enrolled.
    - student_id (int, in the request header): The unique identifier of the student who is enrolling.

    Returns:
    - HTTP_200_OK on success

    Raises:
    - HTTPException (400): If there are no available seats.
    - HTTPException (404): If the specified class or student does not exist.
    - HTTPException (409): If a conflict occurs (e.g., The student has already enrolled into the class).
    - HTTPException (500): If there is an internal server error.
    """

    try:
        class_info = db.execute(
            """
            SELECT course_start_date, enrollment_start, enrollment_end, datetime('now') AS datetime_now, 
                    (room_capacity - COUNT(enrollment.class_id)) AS available_seats
            FROM class LEFT JOIN enrollment ON class.id = enrollment.class_id 
            WHERE class.id = ?;
            """, [class_id]).fetchone()

        if not class_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class Not Found")

        if not (class_info["enrollment_start"] <= class_info["datetime_now"] <= class_info["enrollment_end"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Not Available At The Moment")

        # Insert student if not exists
        db.execute(
            """
            INSERT OR IGNORE INTO student (id, first_name, last_name)
            VALUES (?, ?, ?);
            """, [student_id, first_name, last_name])

        if class_info["available_seats"] <= 0:
            # ----- INSERT INTO WAITLIST TABLE -----
            result = db.execute(
                """
                SELECT COUNT(student_id) 
                FROM waitlist 
                WHERE class_id = ?
                """, [class_id]).fetchone()

            if int(result[0]) >= WAITLIST_CAPACITY:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="No open seats and the waitlist is also full")
            else:
                db.execute(
                    """
                    INSERT INTO waitlist(class_id, student_id, waitlist_date) 
                    VALUES(?, ?, datetime('now'))
                    """, [class_id, student_id]
                )
        else:
            # ----- INSERT INTO ENROLLMENT TABLE -----
            db.execute(
                """
                INSERT INTO enrollment(class_id, student_id, enrollment_date) 
                VALUES(?, ?, datetime('now'))
                """, [class_id, student_id]
            )

        db.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="The student has already enrolled into the class")

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))

    return {"detail": "success"}

@app.delete("/enrollment/{class_id}", status_code=status.HTTP_200_OK)
def drop_class(
    class_id: int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Handles a DELETE request to drop a student (himself/herself) from a specific class.

    Parameters:
    - class_id (int): The ID of the class from which the student wants to drop.
    - student_id (int, in the header): A unique ID for students, instructors, and registrars.

    Returns:
    - dict: A dictionary with the detail message indicating the success of the operation.

    Raises:
    - HTTPException (409): If a conflict occurs
    """
    try:
        curr = db.execute(
            "DELETE FROM enrollment WHERE class_id=? AND student_id=?", [class_id, student_id])

        if curr.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )
        
        db.execute(
            """
            INSERT INTO droplist (class_id, student_id, drop_date, administrative) 
            VALUES (?, ?, datetime('now'), 0);
            """, [class_id, student_id]
        )

        db.commit()

        # Trigger auto enrollment
        if is_auto_enroll_enabled(db):        
            enroll_students_from_waitlist(db, [class_id])

    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"detail": "Item deleted successfully"}

@app.get("/waitlist/{class_id}/position/")
def get_current_waitlist_position(
    class_id:int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: sqlite3.Connection = Depends(get_db)):
    """
    Retreive all available classes.

    Returns:
    - dict: A dictionary containing the details of the classes

    Raises:
    - HTTPException (404): If record not found
    """
    try:
        result = db.execute(
            """
            SELECT COUNT(student_id)
            FROM waitlist
            WHERE class_id=? AND 
                waitlist_date <= (SELECT waitlist_date 
                                    FROM waitlist
                                    WHERE class_id=? AND 
                                            student_id=?)
            ;
            """, [class_id, class_id, student_id]
        ).fetchone()

        if result[0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )
        return {"position": result[0]}
        
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

@app.delete("/waitlist/{class_id}/", status_code=status.HTTP_200_OK)
def remove_from_waitlist(
    class_id: int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Students remove themselves from waitlist

    Parameters:
    - class_id (int): The ID of the class from which the student wants to drop.
    - student_id (int, in the header): A unique ID for students, instructors, and registrars.

    Returns:
    - dict: A dictionary with the detail message indicating the success of the operation.

    Raises:
    - HTTPException (409): If a conflict occurs
    """
    try:
        curr = db.execute(
            "DELETE FROM waitlist WHERE class_id=? AND student_id=?", [class_id, student_id])

        if curr.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )

    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"detail": "Item deleted successfully"}

############### ENDPOINTS FOR INSTRUCTORS ################

@app.get("/classes/{class_id}/students")
def get_current_enrollment(class_id: int,
              instructor_id: int = Header(
                  alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
              db: sqlite3.Connection = Depends(get_db)):
    """
    Retreive current enrollment for the classes.

    Parameters:
    - class_id (int): The ID of the class.

    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        result = db.execute(
            """
            SELECT stu.* 
            FROM class sec
                INNER JOIN enrollment e ON sec.id = e.class_id
                INNER JOIN student stu ON e.student_id = stu.id 
            WHERE sec.id=? AND sec.instructor_id=?
            """, [class_id, instructor_id]
        )
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    finally:
        return {"students": result.fetchall()}

@app.get("/classes/{class_id}/waitlist/")
def get_waitlist(
    class_id:int,
    instructor_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: sqlite3.Connection = Depends(get_db)):
    """
    Retreive current waiting list for the class.

    Parameters:
    - class_id (int): The ID of the class.

    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        result = db.execute(
            """
            SELECT stu.id, stu.first_name, stu.last_name, w.waitlist_date
            FROM class c
                INNER JOIN waitlist w ON c.id = w.class_id
                INNER JOIN student stu ON w.student_id = stu.id 
            WHERE c.id=? AND c.instructor_id=?
            ORDER BY w.waitlist_date ASC
            """, [class_id, instructor_id]
        )
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    finally:
        return {"students": result.fetchall()}

@app.get("/classes/{class_id}/droplist/")
def get_droplist(class_id: int,
              instructor_id: int = Header(
                  alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
              db: sqlite3.Connection = Depends(get_db)):
    """
    Retreive students who have dropped the class.

    Parameters:
    - class_id (int): The ID of the class.
    - instructor_id (int, In the header): A unique ID for students, instructors, and registrars.
    
    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        result = db.execute(
            """
            SELECT stu.* 
            FROM class sec
                INNER JOIN droplist d ON sec.id = d.class_id
                INNER JOIN student stu ON d.student_id = stu.id 
            WHERE sec.id=? AND sec.instructor_id=?
            """, [class_id, instructor_id]
        )
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    finally:
        return {"students": result.fetchall()}

@app.delete("/enrollment/{class_id}/{student_id}/administratively/", status_code=status.HTTP_200_OK)
def drop_class(
    class_id: int,
    student_id: int,
    instructor_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Handles a DELETE request to administratively drop a student from a specific class.

    Parameters:
    - class_id (int): The ID of the class from which the student is being administratively dropped.
    - student_id (int): The ID of the student being administratively dropped.
    - instructor_id (int, In the header): A unique ID for students, instructors, and registrars.

    Returns:
    - dict: A dictionary with the detail message indicating the success of the administrative drop.

    Raises:
    - HTTPException (409): If there is a conflict in the delete operation.
    """
    try:
        curr = db.execute(
            """
            DELETE 
            FROM enrollment
            WHERE class_id = ? AND student_id=? 
                AND class_id IN (SELECT id 
                                    FROM "class" 
                                    WHERE id=? AND instructor_id=?);
            """, [class_id, student_id, class_id, instructor_id])

        if curr.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )
        
        db.execute(
            """
            INSERT INTO droplist (class_id, student_id, drop_date, administrative) 
            VALUES (?, ?, datetime('now'), 1);
            """, [class_id, student_id]
        )
        db.commit()

        # Trigger auto enrollment
        if is_auto_enroll_enabled(db):        
            enroll_students_from_waitlist(db, [class_id])

    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"detail": "Item deleted successfully"}