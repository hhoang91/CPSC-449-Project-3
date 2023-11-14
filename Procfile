gateway: echo ./etc/krakend.json | entr -nrz krakend run --config etc/krakend.json --port $PORT
enrollment_service: uvicorn enrollment_service.app:app --port $PORT --host 0.0.0.0 --reload
user_service: uvicorn user_service.app:app --port $PORT --host 0.0.0.0 --reload
dynamo_db: java -Djava.library.path=dynamodb_local_latest/DynamoDBLocal_lib -jar dynamodb_local_latest/DynamoDBLocal.jar -port $PORT 
# user_service_primary: ./bin/litefs mount -config etc/primary.yml
# user_service_secondary: ./bin/litefs mount -config etc/secondary.yml
# user_service_tertiary: ./bin/litefs mount -config etc/tertiary.yml
dynamodb: sh ./bin/start-dynamodb.sh
redis: sh ./bin/start-redis-server.sh