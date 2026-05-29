"""
Routes:
  POST /auth/register
  POST /auth/login
  GET  /auth/me

  POST /grievances          (public or authenticated)
  GET  /grievances          (authenticated user sees own; admin sees all)
  GET  /grievances/{id}
  PUT  /grievances/{id}     (admin only)
  GET  /grievances/{id}/history

  GET  /admin/dashboard     (admin)
  GET  /admin/export        (admin – CSV download)

  GET  /health
"""

import csv
import io
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_admin_user, get_optional_user,
)
from database import get_db
from ai_classifier import classifier

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_grievance_id() -> str:
    return "GRV-" + uuid.uuid4().hex[:8].upper()


def _log_history(db: Session, grievance: models.Grievance, status: str, note: str, by: str):
    h = models.GrievanceHistory(
        grievance_id=grievance.id,
        status=status,
        note=note,
        changed_by=by,
    )
    db.add(h)


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=schemas.Token, tags=["Auth"])
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")
    user = models.User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/auth/login", response_model=schemas.Token, tags=["Auth"])
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/auth/me", response_model=schemas.UserOut, tags=["Auth"])
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ── Grievances ────────────────────────────────────────────────────────────────

@router.post("/grievances", response_model=schemas.GrievanceOut, tags=["Grievances"])
def submit_grievance(
    payload: schemas.GrievanceCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
):
    # Run AI classification
    ai = classifier.predict(payload.description)

    grievance = models.Grievance(
        grievance_id=_make_grievance_id(),
        user_id=current_user.id if current_user else None,
        name=payload.name,
        phone=payload.phone,
        location=payload.location,
        description=payload.description,
        category=ai["category"],
        priority=ai["priority"],
        status=models.StatusEnum.ai_analyzed,
        department=ai["department"],
        ai_confidence=ai["ai_confidence"],
        ai_sentiment=ai["ai_sentiment"],
    )
    db.add(grievance)
    db.flush()
    _log_history(db, grievance, "submitted", "Grievance submitted", payload.name)
    _log_history(db, grievance, "ai_analyzed",
                 f"AI classified → {ai['department']} | confidence {ai['ai_confidence']:.0%} | sentiment: {ai['ai_sentiment']}",
                 "AI System")
    db.commit()
    db.refresh(grievance)
    return grievance


@router.get("/grievances", response_model=List[schemas.GrievanceOut], tags=["Grievances"])
def list_grievances(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Grievance)
    if not current_user.is_admin:
        q = q.filter(models.Grievance.user_id == current_user.id)
    if status:     q = q.filter(models.Grievance.status == status)
    if priority:   q = q.filter(models.Grievance.priority == priority)
    if category:   q = q.filter(models.Grievance.category == category)
    if department: q = q.filter(models.Grievance.department.ilike(f"%{department}%"))
    return q.order_by(models.Grievance.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/grievances/{grievance_id}", response_model=schemas.GrievanceOut, tags=["Grievances"])
def get_grievance(
    grievance_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    g = db.query(models.Grievance).filter(models.Grievance.grievance_id == grievance_id).first()
    if not g:
        raise HTTPException(404, "Grievance not found")
    if not current_user.is_admin and g.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    return g


@router.put("/grievances/{grievance_id}", response_model=schemas.GrievanceOut, tags=["Grievances"])
def update_grievance(
    grievance_id: str,
    payload: schemas.GrievanceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_admin_user),
):
    g = db.query(models.Grievance).filter(models.Grievance.grievance_id == grievance_id).first()
    if not g:
        raise HTTPException(404, "Grievance not found")

    changes = []
    if payload.status and payload.status != g.status:
        changes.append(f"Status → {payload.status.value}")
        g.status = payload.status
    if payload.priority:   g.priority = payload.priority
    if payload.category:   g.category = payload.category
    if payload.department: g.department = payload.department
    if payload.assigned_to:
        g.assigned_to = payload.assigned_to
        changes.append(f"Assigned to {payload.assigned_to}")
    if payload.resolution_note:
        g.resolution_note = payload.resolution_note

    if changes:
        _log_history(db, g, g.status.value, " | ".join(changes), current_user.name)

    db.commit()
    db.refresh(g)
    return g


@router.get("/grievances/{grievance_id}/history",
            response_model=List[schemas.GrievanceHistoryOut], tags=["Grievances"])
def get_history(
    grievance_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    g = db.query(models.Grievance).filter(models.Grievance.grievance_id == grievance_id).first()
    if not g:
        raise HTTPException(404, "Grievance not found")
    if not current_user.is_admin and g.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    return g.history


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/dashboard", response_model=schemas.DashboardStats, tags=["Admin"])
def dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_admin_user),
):
    q = db.query(models.Grievance)
    total      = q.count()
    submitted  = q.filter(models.Grievance.status == "submitted").count()
    in_progress= q.filter(models.Grievance.status == "in_progress").count()
    resolved   = q.filter(models.Grievance.status == "resolved").count()
    critical   = q.filter(models.Grievance.priority == "critical").count()

    by_category = {
        r[0]: r[1] for r in
        db.query(models.Grievance.category, func.count(models.Grievance.id))
          .group_by(models.Grievance.category).all()
    }
    by_department = {
        r[0]: r[1] for r in
        db.query(models.Grievance.department, func.count(models.Grievance.id))
          .group_by(models.Grievance.department).all()
    }
    recent = q.order_by(models.Grievance.created_at.desc()).limit(10).all()

    return schemas.DashboardStats(
        total=total, submitted=submitted, in_progress=in_progress,
        resolved=resolved, critical=critical,
        by_category={str(k): v for k, v in by_category.items()},
        by_department={str(k): v for k, v in by_department.items()},
        recent=recent,
    )


@router.get("/admin/export", tags=["Admin"])
def export_grievances(
    status:    Optional[str] = None,
    priority:  Optional[str] = None,
    category:  Optional[str] = None,
    date_from: Optional[str] = None,
    date_to:   Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_admin_user),
):
    q = db.query(models.Grievance)
    if status:    q = q.filter(models.Grievance.status == status)
    if priority:  q = q.filter(models.Grievance.priority == priority)
    if category:  q = q.filter(models.Grievance.category == category)
    if date_from: q = q.filter(models.Grievance.created_at >= date_from)
    if date_to:   q = q.filter(models.Grievance.created_at <= date_to)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Phone", "Location", "Description", "Category",
                     "Priority", "Status", "Department", "AI Confidence",
                     "AI Sentiment", "Assigned To", "Resolution Note", "Created"])
    for g in q.all():
        writer.writerow([
            g.grievance_id, g.name, g.phone, g.location,
            g.description[:100], g.category.value, g.priority.value,
            g.status.value, g.department, g.ai_confidence,
            g.ai_sentiment, g.assigned_to, g.resolution_note, g.created_at,
        ])
    output.seek(0)
    return StreamingResponse(
        output, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=grievances.csv"},
    )


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", tags=["System"])
def health():
    return {"status": "ok", "ai_trained": classifier.trained}