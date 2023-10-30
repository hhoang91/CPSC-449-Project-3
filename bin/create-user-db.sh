#!/bin/bash

SCHEMA_PATH="./share/user_schema.sql"
FUSE_DIRECTORY="./var/primary/fuse/"
DB_PATH=$FUSE_DIRECTORY"user.db"

if test -f $DB_PATH; then
	echo "Error: User database already exists."
	exit 1
fi

if ! test -f $SCHEMA_PATH; then
	echo "Error - File Not Found: ${SCHEMA_PATH}"
	exit 1
fi

mkdir -p $FUSE_DIRECTORY
sqlite3 $DB_PATH < $SCHEMA_PATH

if test -f $DB_PATH; then
	echo "User database has been created."
fi