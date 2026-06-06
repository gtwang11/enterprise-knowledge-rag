"""FAQ 相关 Schema"""

from typing import Optional, List
from pydantic import BaseModel, Field


class FaqCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1, max_length=10000)
    category: str = Field(..., min_length=1, max_length=50)
    tags: Optional[str] = None
    keywords: Optional[str] = None


class FaqUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    answer: Optional[str] = Field(None, min_length=1, max_length=10000)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    tags: Optional[str] = None
    keywords: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r'^(published|draft)$')


class FaqOut(BaseModel):
    id: int
    question: str
    answer: str
    category: str
    tags: Optional[str]
    keywords: Optional[str]
    status: str
    version: int
    source_ticket_id: Optional[int]
    created_by: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class FaqQuery(BaseModel):
    keyword: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class FaqBatchDelete(BaseModel):
    ids: List[int] = Field(..., min_length=1)


class ImportResult(BaseModel):
    success_count: int
    skip_count: int
    errors: List[str]
