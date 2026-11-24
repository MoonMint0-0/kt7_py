from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    status: str = Field(default="todo", pattern="^(todo|in_progress|done)$")
    project_id: int


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, pattern="^(todo|in_progress|done)$")


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    project_id: int
    creator_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)