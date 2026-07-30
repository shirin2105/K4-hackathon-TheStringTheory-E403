from datetime import datetime
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class UserQuery(BaseModel):
    """
    Represents an incoming user question and extracted search parameters.
    """
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex[:8]}", description="Unique request tracking ID")
    user_id: str = Field(default="user_demo", description="Discord user ID")
    channel_id: str = Field(default="channel_demo", description="Discord channel ID")
    question: str = Field(..., description="Raw text question submitted by user")
    intent: str = Field(default="unknown", description="Classified intent (deadline, schedule, etc.)")
    cohort: str = Field(default="UNKNOWN", description="Extracted cohort (K2, K3, K4, ALL, UNKNOWN)")
    topic: Optional[str] = Field(default=None, description="Extracted topic (e.g. Gate 1, Workshop)")
    date_reference: Optional[str] = Field(default=None, description="Extracted date term (e.g. tối nay, tuần sau)")
    resource_type: Optional[str] = Field(default=None, description="Extracted resource type (e.g. slide, repo, link)")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Request creation timestamp")
