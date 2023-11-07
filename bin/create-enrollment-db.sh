#!/bin/bash

SCHEMA_PATH="./share/enrollment_schema.sql"
SAMPLE_DATA_PATH="./share/enrollment_sample_data.sql"
DB_DIRECTORY="./var/"
DB_FILENAME="enrollment_local.db"
DB_PATH="$DB_DIRECTORY$DB_FILENAME"

if test -f $DB_PATH; then
	echo "Error: Enrollment database already exists."
	exit 1
fi

if ! test -f $SCHEMA_PATH; then
	echo "Error - File Not Found: ${SCHEMA_PATH}"
	exit 1
fi

mkdir -p $DB_DIRECTORY
sqlite3 $DB_PATH < $SCHEMA_PATH
sqlite3 $DB_PATH < $SAMPLE_DATA_PATH

if test -f $DB_PATH; then
	echo "Enrollment database has been created."
fi
