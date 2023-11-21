from fastapi import FastAPI
from .student_router import student_router
from .instructor_router import instructor_router
from .registrar_router import registrar_router

# Create the main FastAPI application instance
app = FastAPI()

# Attach the routers to the main application
app.include_router(student_router)
app.include_router(instructor_router)
app.include_router(registrar_router)
