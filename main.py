import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import User, Workout, WorkoutExercise, ExerciseSet, Challenge

app = FastAPI(title="FitTrack API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"name": "FitTrack API", "status": "ok"}

# Utility: compute derived metrics for a workout

def compute_workout_metrics(workout: Workout) -> Workout:
    total_volume = 0.0
    total_sets = 0
    total_reps = 0
    for ex in workout.exercises:
        for s in ex.sets:
            total_sets += 1
            total_reps += s.reps
            total_volume += (s.reps * (s.weight or 0))
    workout.total_volume = round(total_volume, 2)
    workout.total_sets = total_sets
    workout.total_reps = total_reps
    if workout.date is None:
        workout.date = datetime.now(timezone.utc)
    if workout.likes is None:
        workout.likes = 0
    return workout

# Auth light placeholder (username only for demo)
class CreateUserRequest(BaseModel):
    username: str
    full_name: Optional[str] = None
    city: Optional[str] = None

@app.post("/api/users")
def create_user(payload: CreateUserRequest):
    # ensure unique username
    existing = db["user"].find_one({"username": payload.username}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(username=payload.username, full_name=payload.full_name, city=payload.city)
    user_id = create_document("user", user)
    return {"id": user_id, "username": user.username}

@app.get("/api/users")
def list_users(limit: int = 20):
    users = get_documents("user", {}, limit)
    for u in users:
        u["_id"] = str(u["_id"])  # stringify ids
    return users

# Workouts
class CreateWorkoutRequest(Workout):
    pass

@app.post("/api/workouts")
def create_workout(payload: CreateWorkoutRequest):
    workout = compute_workout_metrics(payload)
    workout_id = create_document("workout", workout)
    return {"id": workout_id, "total_volume": workout.total_volume}

@app.get("/api/workouts")
def get_feed(user: Optional[str] = None, limit: int = 20):
    query = {"user_id": user} if user else {}
    workouts = db["workout"].find(query).sort("date", -1).limit(limit)
    result = []
    for w in workouts:
        w["_id"] = str(w["_id"])  # stringify
        result.append(w)
    return result

@app.post("/api/workouts/{workout_id}/like")
def like_workout(workout_id: str):
    doc = db["workout"].find_one({"_id": {"$eq": db["workout"]._pk_factory(workout_id)} }) if False else None
    # Simple atomic increment without needing ObjectId conversion helpers in this template
    updated = db["workout"].find_one_and_update({"_id": {"$exists": True}, "_id": {"$type": "objectId"}, "$expr": {"$eq": ["$_id", {"$toObjectId": workout_id}] }}, {"$inc": {"likes": 1}}, return_document=True)
    # Fallback naive approach if above pipeline isn't supported in env
    if not updated:
        try:
            from bson import ObjectId
            updated = db["workout"].find_one_and_update({"_id": ObjectId(workout_id)}, {"$inc": {"likes": 1}}, return_document=True)
        except Exception:
            pass
    if not updated:
        raise HTTPException(status_code=404, detail="Workout not found")
    updated["_id"] = str(updated["_id"])
    return updated

# Challenges
@app.post("/api/challenges")
def create_challenge(challenge: Challenge):
    challenge_id = create_document("challenge", challenge)
    return {"id": challenge_id}

@app.get("/api/challenges")
def list_challenges(limit: int = 20):
    docs = get_documents("challenge", {}, limit)
    for d in docs:
        d["_id"] = str(d["_id"])  # stringify ids
    return docs

# Public schema explorer for Flames DB UI
@app.get("/schema")
def get_schema_overview():
    return {
        "collections": [
            "user",
            "workout",
            "challenge"
        ]
    }

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
