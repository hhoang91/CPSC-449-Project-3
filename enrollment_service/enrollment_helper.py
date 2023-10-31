import sqlite3
from fastapi import HTTPException, status

def is_auto_enroll_enabled(db: sqlite3.Connection):
    """
    Check if automatic enrollment is enabled

    Parameters:
        db (sqlite3.Connection): Database connection.

    Returns:
        bool: True if automatic enrollment is enabled. Otherwise, False.
    """
    
    cursor = db.execute("SELECT automatic_enrollment FROM configs")
    result = cursor.fetchone()
    return result[0] == 1

def get_opening_classes(db: sqlite3.Connection):
    """
    Get sections which have available seats

    Parameters:
        db (sqlite3.Connection): Database connection.

    Returns:
        list[int]: A list of section_id.
    """

    cursor = db.execute(
        """
        SELECT id 
        FROM section 
        WHERE DATE('now') <= date(course_start_date, '+14 days') AND
            room_capacity > (SELECT COUNT(student_id)
                            FROM enrollment
                            WHERE section_id = id
                            )
        """)
    rows = cursor.fetchall()
    return [row[0] for row in rows]

def enroll_students_from_waitlist(db: sqlite3.Connection, section_id_list: list[int]):
    """
    This function checks the waitlist for available spots in the sections
    and enrolls students accordingly.

    Parameters:
        db (sqlite3.Connection): Database connection.

    Returns:
        int: The number of success enrollments.
    """
    
    enrollment_count = 0

    try:
        for e in section_id_list:
            cursor = db.execute(
            """
            INSERT INTO enrollment (section_id, student_id, enrollment_date)
                SELECT section_id, student_id, datetime('now')
                FROM waitlist
                WHERE section_id=$0
                ORDER BY waitlist_date ASC
                LIMIT (
                        (SELECT room_capacity 
                        FROM section
                        WHERE id=$0) - (SELECT COUNT(student_id)
                                        FROM enrollment
                                        WHERE section_id=$0
                                        )
                    );
            """, [e])

            cursor = db.execute(
            """
            DELETE FROM waitlist
            WHERE student_id IN (
                SELECT student_id
                FROM waitlist
                ORDER BY waitlist_date
                LIMIT $0
            );
            """, [cursor.rowcount])

            enrollment_count += cursor.rowcount
        
        db.commit()
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )
    return enrollment_count