from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class SourceMessage(BaseModel):
    """
    Represents a source announcement message stored in Discord or database.
    """
    id: str = Field(..., description="Unique message identifier, e.g. msg_001")
    channel_name: str = Field(..., description="Discord channel name without #, e.g. venture-arena")
    channel_id: str = Field(..., description="Discord channel ID string")
    message_url: str = Field(..., description="Direct URL link to Discord message or document")
    author_name: str = Field(default="Ban Tổ Chức", description="Author display name")
    author_role: Literal["official", "mod", "mentor", "student"] = Field(
        default="official", description="Role authority level"
    )
    content: str = Field(..., description="Full text content of announcement or document")
    topic: str = Field(..., description="Associated topic (e.g. Gate 1, Workshop)")
    intent: str = Field(..., description="Associated intent (e.g. deadline, schedule)")
    cohort: str = Field(default="ALL", description="Target cohort (K2, K3, K4, ALL, UNKNOWN)")
    posted_at: str = Field(..., description="ISO 8601 or human posting timestamp")
    status: Literal["active", "updated", "superseded", "expired"] = Field(
        default="active", description="Current status of the announcement"
    )
    supersedes_source_id: Optional[str] = Field(
        default=None, description="ID of older source message replaced by this one"
    )

    def parse_posted_at(self) -> datetime:
        """Parse datetime string into naive datetime object for safe comparisons."""
        val = str(self.posted_at).strip()

        # Handle ISO strings
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        except Exception:
            pass

        # Try parsing human date formats
        date_formats = [
            "%A, %B %d, %Y %I:%M %p",
            "%B %d, %Y %I:%M %p",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d"
        ]
        for fmt in date_formats:
            try:
                dt = datetime.strptime(val.split("+")[0].split(".")[0], fmt)
                return dt.replace(tzinfo=None)
            except Exception:
                continue

        return datetime(2026, 7, 1)

    @property
    def is_active(self) -> bool:
        return self.status in ["active", "updated"]

    @property
    def is_superseded(self) -> bool:
        return self.status == "superseded"

    @property
    def is_expired(self) -> bool:
        return self.status == "expired"
