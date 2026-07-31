from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from models.message import SourceMessage


class DecisionStatus(str, Enum):
    VERIFIED = "VERIFIED"
    VERIFIED_WITH_CONFLICT_RESOLVED = "VERIFIED_WITH_CONFLICT_RESOLVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class RejectedSource(BaseModel):
    source: SourceMessage
    reason: str


class DecisionResult(BaseModel):
    """
    Final output produced by DecisionEngine.
    """
    status: DecisionStatus
    answer: str
    selected_source: Optional[SourceMessage] = None
    rejected_sources: List[RejectedSource] = Field(default_factory=list)
    candidate_sources: List[SourceMessage] = Field(default_factory=list)
    confidence: float = Field(default=0.0, description="Confidence score between 0.0 and 1.0")
    confidence_level: str = Field(default="low", description="high (>=80), medium (60-79), insufficient (<60)")
    needs_mod: bool = Field(default=False, description="Flag indicating mod escalation recommendation")
    should_show_source_link: bool = Field(default=False, description="Whether the verified source should be shown to the user")
    verification_details: Dict[str, Any] = Field(default_factory=dict, description="Metadata explaining verification steps")
