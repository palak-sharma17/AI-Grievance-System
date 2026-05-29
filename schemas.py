from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import PriorityEnum, StatusEnum, CategoryEnum


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ── Grievance ─────────────────────────────────────────────────────────────────

class GrievanceCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    location: str
    description: str


class GrievanceUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None
    category: Optional[CategoryEnum] = None
    department: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_note: Optional[str] = None


class GrievanceHistoryOut(BaseModel):
    id: int
    status: str
    note: Optional[str]
    changed_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class GrievanceOut(BaseModel):
    id: int
    grievance_id: str
    name: str
    phone: Optional[str]
    location: str
    description: str
    category: CategoryEnum
    priority: PriorityEnum
    status: StatusEnum
    department: Optional[str]
    ai_confidence: float
    ai_sentiment: str
    assigned_to: Optional[str]
    resolution_note: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    history: List[GrievanceHistoryOut] = []

    class Config:
        from_attributes = True


# ── Stats ─────────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total: int
    submitted: int
    in_progress: int
    resolved: int
    critical: int
    by_category: dict
    by_department: dict
    recent: List[GrievanceOut]