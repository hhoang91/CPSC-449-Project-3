import os
import requests
from settings import *

def unittest_setUp():
    if USING_LITEFS_TO_REPLICATE_USER_DATABASE:
        # ------- If you're using LiteFS, READ ME -----------
        # In case of using LiteFS to replicate user service database,
        # the data in user database will be reset.

        # Delete the current database, then create a new one
        os.system(f"[ ! -f {USER_DB_PATH} ] || rm {USER_DB_PATH}")
        os.system("sh ./bin/create-user-db.sh > /dev/null")
    else:
        # Backup the current database, then create a new one
        os.system(f"[ ! -f {USER_DB_PATH} ] || cp {USER_DB_PATH} {USER_DB_PATH}.backup")
        os.system("sh ./bin/create-user-db.sh > /dev/null")

def unittest_tearDown():
    if USING_LITEFS_TO_REPLICATE_USER_DATABASE:
        os.system(f"[ ! -f {USER_DB_PATH} ] || rm {USER_DB_PATH}")
        os.system("sh ./bin/create-user-db.sh > /dev/null")
    else:
        # Restore database
        os.system(f"rm -f {USER_DB_PATH}")
        os.system(f"[ ! -f {USER_DB_PATH}.backup ] || mv {USER_DB_PATH}.backup {USER_DB_PATH}")

def user_register(username, password, first_name, last_name, roles: list[str]):
    url = f'{BASE_URL}/api/register'
    myobj = {
        "id": 2,
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "roles": roles
    }
    res = requests.post(url, json = myobj)
    data = res.json()
    return "message" in data

def user_login(username, password):
    url = f'{BASE_URL}/api/login'
    myobj = {
        "username": username,
        "password": password
    }
    res = requests.post(url, json = myobj)
    data = res.json()
    if "access_token" in data:
        return data["access_token"]
    
    return None