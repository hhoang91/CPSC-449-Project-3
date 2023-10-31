PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;

DROP TABLE IF EXISTS configs;
CREATE TABLE configs (
	automatic_enrollment BOOLEAN NOT NULL
);

DROP TABLE IF EXISTS department;
CREATE TABLE department (
	code TEXT PRIMARY KEY, 
	dept_name TEXT NOT NULL
);

DROP TABLE IF EXISTS instructor;
CREATE TABLE instructor (
	id INTEGER PRIMARY KEY,
	first_name TEXT NOT NULL,
	last_name TEXT NOT NULL
);

DROP TABLE IF EXISTS student;
CREATE TABLE student (
	id INTEGER PRIMARY KEY,
	first_name TEXT NOT NULL,
	last_name TEXT NOT NULL
);

DROP TABLE IF EXISTS course;
CREATE TABLE course (
	department_code TEXT NOT NULL REFERENCES department(code),
	course_no INTEGER NOT NULL,
	title TEXT NOT NULL,
	PRIMARY KEY (department_code, course_no)
);

CREATE TABLE section (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	dept_code TEXT NOT NULL,
	course_num INTEGER NOT NULL,
	section_no INTEGER NOT NULL,
	academic_year INTEGER NOT NULL,
	semester TEXT NOT NULL,
	instructor_id INTEGER NOT NULL REFERENCES instructor(id),
	room_num INTEGER NOT NULL,
	room_capacity INTEGER NOT NULL,
	course_start_date TEXT NOT NULL,
	enrollment_start TEXT NOT NULL,
	enrollment_end TEXT NOT NULL,
	UNIQUE (dept_code, course_num, section_no, academic_year, semester),
	FOREIGN KEY (dept_code, course_num) REFERENCES course(department_code, course_no)
);

DROP TABLE IF EXISTS enrollment;
CREATE TABLE enrollment (
	section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE RESTRICT ON UPDATE CASCADE,
	student_id INTEGER NOT NULL REFERENCES student(id),
	enrollment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(section_id, student_id)
);

DROP TABLE IF EXISTS waitlist;
CREATE TABLE waitlist (
	section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE ON UPDATE CASCADE,
	student_id INTEGER NOT NULL REFERENCES student(id),
	waitlist_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(section_id, student_id)
);

DROP TABLE IF EXISTS droplist;
CREATE TABLE droplist (
	section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE RESTRICT ON UPDATE CASCADE,
	student_id INTEGER NOT NULL REFERENCES student(id),
	drop_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	administrative BOOLEAN NOT NULL DEFAULT FALSE,
	PRIMARY KEY(section_id, student_id)
);

COMMIT;