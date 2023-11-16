import redis
import datetime
import time
from datetime import datetime

redis_conn = redis.Redis(decode_responses=True)
if redis_conn.exists("waitlist"):
    redis_conn.delete("waitlist")

# Data to be inserted
waitlist_data = [
    {"class_id": 2, "student_id": 65123456, "waitlist_date": '2023-08-28 09:00:00'},
    {"class_id": 2, "student_id": 73123456, "waitlist_date": '2023-08-28 10:00:00'},
    {"class_id": 2, "student_id": 76123456, "waitlist_date": '2023-08-28 11:30:00'},
    {"class_id": 2, "student_id": 68123456, "waitlist_date": '2023-08-29 09:40:00'},
    {"class_id": 2, "student_id": 85123456, "waitlist_date": '2023-08-29 09:50:00'}
]

# ZADD <key> <score> <member>
waitlist_key = "waitlist"
for entry in waitlist_data:
    class_id = entry["class_id"]
    student_id = entry["student_id"]
    waitlist_date = entry["waitlist_date"]
    
    # Construct the member using class_id and student_id
    member = f"{class_id}_{student_id}"

    # Convert waitlist_date to a float
    waitlist_date = datetime.strptime(waitlist_date, '%Y-%m-%d %H:%M:%S')
    score = waitlist_date.timestamp()
  
    # Add the member and score to the sorted set
    redis_conn.zadd(waitlist_key, {member: score})

# Retrieve and print the sorted set
result = redis_conn.zrange(waitlist_key, 0, -1, withscores=True)
for member, score in result:
    print(f"Member: {member}, Score: {score}")