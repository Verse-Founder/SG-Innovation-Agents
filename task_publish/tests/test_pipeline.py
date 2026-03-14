import asyncio
import json
from task_publish.db.session import engine, SessionLocal
from task_publish.db.models import Base, User, DynamicTaskRule
from task_publish.task_agent import agent_orchestrator
from task_publish.api.routes import get_active_dynamic_task, select_destination, arrive_at_destination, SelectDestinationReq, ArriveReq
from sqlalchemy import text

def setup_mock_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Create a user
    user = User(user_id="test_user_1", name="Test User", language_pref="en")
    db.add(user)
    
    # 2. Create a global rule
    rule = DynamicTaskRule(user_id=None, base_calorie=300, trigger_threshold=0.6, exercise_pts=50)
    db.add(rule)
    db.commit()
    return db

async def test_run_pipeline():
    db = setup_mock_db()
    
    print("--- 1. Admin triggers task ---")
    agent_orchestrator.run(db, user_id="test_user_1", trigger_source="admin")
    
    print("--- 2. App gets active task ---")
    active_task = get_active_dynamic_task(user_id="test_user_1", db=db)
    print("Active Task Response:", json.dumps(active_task, indent=2))
    task_id = active_task.get("task_id")
    
    if not task_id:
        print("FAIL: No task generated.")
        return

    print("--- 3. User selects a park ---")
    req = SelectDestinationReq(park_index=0)
    await select_destination(task_id=task_id, req=req, user_id="test_user_1", db=db)
    
    print("--- 4. App gets active task again (Pending) ---")
    pending_task = get_active_dynamic_task(user_id="test_user_1", db=db)
    print("Pending Task Response:", json.dumps(pending_task, indent=2))
    park = pending_task["destination"]
    
    print(f"--- 5. User arrives at {park['name']} ---")
    arrive_req = ArriveReq(lat=park["lat"], lng=park["lng"])
    res = arrive_at_destination(task_id=task_id, req=arrive_req, db=db)
    print("Arrival Result:", res)

    print("--- 6. Check points ---")
    from task_publish.api.routes import get_points_summary
    points = get_points_summary(user_id="test_user_1", db=db)
    print("Points Summary:", points)

if __name__ == "__main__":
    asyncio.run(test_run_pipeline())
