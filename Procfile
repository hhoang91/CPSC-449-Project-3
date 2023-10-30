enrollment_service: uvicorn enrollment_service.app:app --port $PORT --host 0.0.0.0 --reload
user_service: uvicorn user_service.app:app --port $PORT --host 0.0.0.0 --reload
# worker: echo ./etc/krakend.json | entr -nrz krakend run --config etc/krakend.json --port $PORT
# login_service_primary: ./bin/litefs mount -config etc/primary.yml
# login_secondary: ./bin/litefs mount -config etc/secondary.yml
# login_tertiary: ./bin/litefs mount -config etc/tertiary.yml