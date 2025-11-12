"""
Database Schemas for FitTrack

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Users of the platform
class User(BaseModel):
    username: str = Field(..., description="Public handle, unique per user")
    full_name: Optional[str] = Field(None, description="Full name")
    bio: Optional[str] = Field(None, description="Short bio")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    city: Optional[str] = Field(None, description="City or gym location")
    level: Optional[str] = Field("beginner", description="Training level: beginner/intermediate/advanced")
    goals: Optional[List[str]] = Field(default_factory=list, description="Fitness goals")

# One set inside an exercise
class ExerciseSet(BaseModel):
    reps: int = Field(..., ge=1, description="Repetitions")
    weight: float = Field(0, ge=0, description="Weight in kg")
    rest_sec: Optional[int] = Field(90, ge=0, description="Rest in seconds")
    rpe: Optional[float] = Field(None, ge=1, le=10, description="Rate of Perceived Exertion 1-10")

# An exercise inside a workout session
class WorkoutExercise(BaseModel):
    name: str = Field(..., description="Exercise name, e.g., Bench Press")
    sets: List[ExerciseSet] = Field(default_factory=list, description="Sets performed")

# A logged workout session
class Workout(BaseModel):
    user_id: str = Field(..., description="ID or username of the athlete")
    notes: Optional[str] = Field(None, description="Optional notes for the session")
    duration_min: Optional[int] = Field(None, ge=0, description="Duration in minutes")
    fatigue: Optional[int] = Field(None, ge=1, le=10, description="Post-session fatigue 1-10")
    exercises: List[WorkoutExercise] = Field(default_factory=list)
    # Derived metrics (filled by backend for fast leaderboard)
    total_volume: Optional[float] = Field(None, ge=0, description="Sum of reps*weight across all sets")
    total_sets: Optional[int] = Field(None, ge=0)
    total_reps: Optional[int] = Field(None, ge=0)
    date: Optional[datetime] = Field(None, description="Session timestamp")
    likes: Optional[int] = Field(0, ge=0, description="Like/reaction counter")
    media_url: Optional[str] = Field(None, description="Optional photo/clip URL")

# Monthly/weekly challenges
class Challenge(BaseModel):
    title: str = Field(..., description="Challenge name")
    description: Optional[str] = Field(None)
    metric: str = Field(..., description="What we count: e.g., reps, volume, distance")
    target: float = Field(..., ge=0, description="Target value to complete the challenge")
    period: str = Field("monthly", description="weekly/monthly")
    starts_at: Optional[datetime] = Field(None)
    ends_at: Optional[datetime] = Field(None)

# Lightweight reaction schema (optional use)
class Reaction(BaseModel):
    workout_id: str = Field(...)
    type: str = Field("like", description="like/🔥/💪 etc.")
    user_id: Optional[str] = Field(None)
