#!/bin/bash

SCHEMA_PATH="./share/enrollment_schema.sql"
SAMPLE_DATA_PATH="./share/enrollment_sample_data.sql"
ENV_FILE=".env"

# Check if ENV_FILE exists
if [ ! -f $ENV_FILE ]; then
	echo "\e[31mError: .env File Not Found\e[0m"
	echo "To create .env file, run this command:"
	echo '   "sh ./bin/create-dotenv.sh"'
	exit 1
fi

# Load ENV_FILE
export $(grep -v '^#' $ENV_FILE | xargs)

if [ -f $ENROLLMENT_SERVICE_DB_PATH ]; then
	echo "Error: Enrollment database already exists."
	exit 1
fi

if [ ! -f $SCHEMA_PATH ]; then
	echo "Error - File Not Found: ${SCHEMA_PATH}"
	exit 1
fi

mkdir -p "$(dirname $ENROLLMENT_SERVICE_DB_PATH)"
sqlite3 $ENROLLMENT_SERVICE_DB_PATH < $SCHEMA_PATH
sqlite3 $ENROLLMENT_SERVICE_DB_PATH < $SAMPLE_DATA_PATH

if [ -f $ENROLLMENT_SERVICE_DB_PATH ]; then
	echo "Enrollment database has been created."
fi