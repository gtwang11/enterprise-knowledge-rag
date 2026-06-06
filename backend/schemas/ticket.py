"""工单相关 Schema"""

from typing import Optional
from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    supplementary: Optional[str] = Field(None, max_length=2000)
    urgency: str = Field("normal", pattern=r'^(normal|urgent|emergency)$')


class TicketOut(BaseModel):
    id: int
    ticket_no: str
    question: str
    supplementary: Optional[str]
    urgency: str
    status: str
    submitter_id: int
    handler_id: Optional[int]
    solution: Optional[str]
    reject_reason: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TicketDetailOut(TicketOut):
    submitter_name: Optional[str] = None
    handler_name: Optional[str] = None
    timeline: list = []


class TicketQuery(BaseModel):
    status: Optional[str] = None
    urgency: Optional[str] = None
    keyword: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class SolutionRequest(BaseModel):
    solution: str = Field(..., min_length=1, max_length=10000)


class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class PublishFaqRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1, max_length=10000)
    category: str = Field("工单转换", max_length=50)
    overwrite: bool = False
