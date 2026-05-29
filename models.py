from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class PriorityEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class StatusEnum(str, enum.Enum):
    submitted = "submitted"
    ai_analyzed = "ai_analyzed"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"
    rejected = "rejected"


class CategoryEnum(str, enum.Enum):
    water = "Water Supply"
    road = "Road & Infrastructure"
    sanitation = "Sanitation & Waste"
    electricity = "Electricity"
    safety = "Public Safety"
    health = "Health & Hygiene"
    transport = "Transport"
    other = "Other"


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, index=True, nullable=False)
    phone      = Column(String(20))
    password   = Column(String(255), nullable=False)
    is_admin   = Column(Boolean, default=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    grievances = relationship("Grievance", back_populates="user")


class Grievance(Base):
    __tablename__ = "grievances"

    id              = Column(Integer, primary_key=True, index=True)
    grievance_id    = Column(String(20), unique=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=True)
    name            = Column(String(100), nullable=False)
    phone           = Column(String(20))
    location        = Column(String(255), nullable=False)
    description     = Column(Text, nullable=False)
    category        = Column(Enum(CategoryEnum), default=CategoryEnum.other)
    priority        = Column(Enum(PriorityEnum), default=PriorityEnum.medium)
    status          = Column(Enum(StatusEnum), default=StatusEnum.submitted)
    department      = Column(String(100))
    ai_confidence   = Column(Float, default=0.0)
    ai_sentiment    = Column(String(20), default="neutral")
    image_url       = Column(String(500), nullable=True)
    assigned_to     = Column(String(100), nullable=True)
    resolution_note = Column(Text, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    user    = relationship("User", back_populates="grievances")
    history = relationship("GrievanceHistory", back_populates="grievance")


class GrievanceHistory(Base):
    __tablename__ = "grievance_history"

    id           = Column(Integer, primary_key=True, index=True)
    grievance_id = Column(Integer, ForeignKey("grievances.id"))
    status       = Column(String(50))
    note         = Column(Text)
    changed_by   = Column(String(100))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    grievance = relationship("Grievance", back_populates="history")