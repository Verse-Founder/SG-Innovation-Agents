from fastapi import FastAPI
from task_publish.api.routes import router
from task_publish.db.session import engine, Base

import task_publish.db.models  # to attach metadata

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Publication API v3.1")

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
