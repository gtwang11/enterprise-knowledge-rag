"""问答相关 Schema"""

from typing import Optional, List
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    has_answer: bool
    answer: Optional[str] = None
    similarity: float
    references: List[dict] = []
    message: Optional[str] = None


class QaHistoryOut(BaseModel):
    id: int
    question: str
    answer: Optional[str]
    has_answer: bool
    similarity_score: Optional[float]
    processing_time_ms: int
    created_at: str

    class Config:
        from_attributes = True


class QaHistoryQuery(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
