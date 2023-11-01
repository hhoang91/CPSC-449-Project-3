# Student Enrollment
Create a new user authentication service with read replication, then use it to implement authentication and load balancing through an API gateway.

## Installation
run `sh ./bin/install.sh`.

## How to run
- run `sh run.sh` to start the services.
- run `sh ./bin/create-user-db.sh` to create user database.
- run `sh ./bin/create-enrollment-db.sh` to create enrollment service database.

## Database ER Diagram
#### User Service
<img src="https://github.com/NLTN/Assets/blob/main/StudentEnrollment/UserERDiagram.png?raw=true">

#### Enrollment Service
<img src="https://github.com/NLTN/Assets/blob/main/StudentEnrollment/EnrollmentERDiagram.png?raw=true">

## API Gateway endpoints
#### For User Service
| Method | Route            | Description                   |
|--------|------------------|-------------------------------|
|POST    | /api/register/	| Register a new user account.	|
|POST    | /api/login/		| User login.                   |

#### For registras
| Method | Route                    | Description                               |
|--------|--------------------------|-------------------------------------------|
|PUT     | /api/auto-enrollment/    | Turn auto enrollment on/off.              |
|POST    | /api/courses/            | Creates a new course.                     |
|POST    | /api/classes/            | Creates a new class.                      |
|DELETE  | /api/classes/{class_id}  | Deletes a specific class.                 |
|PATCH   | /api/classes/{class_id}  | Updates specific details of a class.      |


#### For students
| Method | Route                                | Description                                |
|--------|--------------------------------------|--------------------------------------------|
|GET     | /api/classes/available/              | Retreive all available classes.            |
|GET     | /api/waitlist/{class_id}/position/   | Get current waitlist position.             |
|POST    | /api/enrollment/                     | Student enrolls in a class.                |
|DELETE  | /api/enrollment/{class_id}           | Students drop themselves from a class.     |
|DELETE  | /api/waitlist/{class_id}             | Students remove themselves from a waitlist.|

#### For instructors
| Method | Route                                | Description                               |
|--------|--------------------------------------|-------------------------------------------|
|GET     | /api/classes/{class_id}/students/    | Retreive current enrollment for the classes.  |
|GET     | /api/classes/{class_id}/droplist/    | Retreive students who have dropped the class  |
|GET     | /api/classes/{class_id}/waitlist/    | Retreive students in the waitling list        |
|DELETE  | /api/enrollment/{class_id}/{student_id}/administratively/   | Instructors drop students administratively. |
