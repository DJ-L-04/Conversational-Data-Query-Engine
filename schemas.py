from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    original_filename: str
    file_type: str
    row_count: Optional[int]
    column_count: Optional[int]
    columns: Optional[List[str]]
    file_size_kb: Optional[float]
    uploaded_at: datetime

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    file_id: uuid.UUID
    question: str
    model: Optional[str] = "gpt-3.5-turbo"


class QueryResponse(BaseModel):
    answer: str
    file_id: uuid.UUID
    question: str
    model_used: str
    cached: bool
    response_time_ms: float


class QueryHistoryResponse(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    model_used: Optional[str]
    cached: bool
    response_time_ms: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
