from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnimalCreate(BaseModel):
    identifier: str = Field(min_length=1, max_length=80)
    breed: str | None = Field(default=None, max_length=80)
    age_months: int | None = Field(default=None, ge=0, le=600)
    days_in_milk: int | None = Field(default=None, ge=0, le=1500)
    productive_state: str | None = Field(default=None, pattern="^(lactating|dry)$")
    transition_stage: str | None = Field(default=None, pattern="^(outside|prepartum|postpartum|unknown)$")
    notes: str | None = Field(default=None, max_length=500)


class Animal(AnimalCreate):
    id: int
    created_at: datetime


class AssessmentCreate(BaseModel):
    animal_id: int | None = None
    answers: dict[str, Any]


class Assessment(BaseModel):
    id: int
    animal_id: int | None
    created_at: datetime
    answers: dict[str, Any]
    result: dict[str, Any]
    follow_up: str | None = None


class FollowUpUpdate(BaseModel):
    follow_up: str = Field(min_length=1, max_length=1000)
