from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from task_publish.api.routes import router
from task_publish.db.session import engine
from task_publish.db.models import Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Publication API v3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
