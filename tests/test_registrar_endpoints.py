import os
import unittest
import requests
from helper import user_register, user_login, unittest_setUp, unittest_tearDown
from settings import BASE_URL, USER_DB_PATH, ENROLLMENT_DB_PATH

class AutoEnrollmentTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()
    
    def tearDown(self):
        unittest_tearDown()

    def test_enable_auto_enrollment(self):
        # 1. Register & Login
        user_register("nathan", "1234", "nathan", "nguyen", ["Student", "Registrar"])
        access_token = user_login(username="nathan", password="1234")
        
        # 2. Prepare header & message body        
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "enabled": True
        }

        # 3. Send request
        url = f'{BASE_URL}/api/auto-enrollment/'
        response = requests.put(url, headers=headers, json=body)
        
        # 4. Asserts
        self.assertEquals(response.status_code, 200)
        self.assertIn("detail", response.json())

    def test_disable_auto_enrollment(self):
        # 1. Register & Login
        user_register("nathan", "1234", "nathan", "nguyen", ["Student", "Registrar"])
        access_token = user_login(username="nathan", password="1234")
        
        # 2. Prepare header & message body        
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "enabled": False
        }

        # 3. Send request
        url = f'{BASE_URL}/api/auto-enrollment/'
        response = requests.put(url, headers=headers, json=body)
        
        # 4. Asserts
        self.assertEquals(response.status_code, 200)
        self.assertIn("detail", response.json())
     
if __name__ == '__main__':
    unittest.main()