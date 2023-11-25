#!/bin/sh

# Check if redis is listening to port 6379
REDIS_PORT_CHECK=$(netstat -nltp | grep 6379)

if [ -n "$REDIS_PORT_CHECK" ]; then
    # If Redis is running, stop the service
    service redis-server stop
fi

# Create .env file
sh ./bin/create-dotenv.sh

# Create user database if not exists
sh ./bin/create-user-db.sh

# Start the services
foreman start -m gateway=1,enrollment_service=3,user_service=1,dynamodb=1,redis=1
