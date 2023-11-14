import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Base(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier")
    created_at: Optional[datetime] = Field(None, description="Creation datetime")
    updated_at: Optional[datetime] = Field(None, description="Update datetime")


class FundDocumentMetadata(BaseModel):
    fund_name: Optional[str]
    fund_ticker: Optional[str]
    document_description: Optional[str]


class Document(Base):
    url: str
    metadata: Optional[FundDocumentMetadata]
