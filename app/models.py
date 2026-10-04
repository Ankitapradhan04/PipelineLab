from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120)
    priority: Priority = Priority.medium


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=120)
    priority: Priority | None = None
    done: bool | None = None


class Task(BaseModel):
    id: int
    title: str
    priority: Priority
    done: bool = False
    created_at: datetime


class Stats(BaseModel):
    total: int
    done: int
    open: int
    by_priority: dict[str, int]
