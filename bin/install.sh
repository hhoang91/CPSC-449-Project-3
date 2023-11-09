#!/bin/bash

# Update package lists
sudo apt update

# Install SQLite3
sudo apt install -y sqlite3

# Install ruby-foreman
sudo apt install -y ruby-foreman

# Install entr
sudo apt install -y entr

# ***** Block to install KrakenD *****
# Add the GPG key for the specified keyserver
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 5DE6FD698AD6FDD2

# Add Krakend repository to sources list
sudo echo "deb https://repo.krakend.io/apt stable main" | sudo tee /etc/apt/sources.list.d/krakend.list

# Update package lists
sudo apt update

# Install KrakenD
sudo apt install -y krakend
# *************************************

# Install HTTPie for Terminal to work with REST APIs
sudo apt install -y httpie

# Install pip for Python 3
sudo apt install -y python3-pip

# Install required libaries for the project
pip3 install -r requirements.txt

# Install the aws cli
sudo ./aws/install

# Configure dummy credentials for DynamoDB local 
AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DEFAULT_REGION="us-west-2"
DEFAULT_OUTPUT_FORMAT="json"

# Run 'aws configure'
aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
aws configure set default.region "$DEFAULT_REGION"
aws configure set default.output "$DEFAULT_OUTPUT_FORMAT"

# Install Java Runtime Environment
sudo apt install --yes openjdk-19-jre-headless

# Print 'Installation Successful'
echo "\n\n"
echo "*****************************************"
echo "*        Installation Successful        *"
echo "*****************************************"
echo "To start the servers, run: 'sh run.sh'"
echo "\n" 