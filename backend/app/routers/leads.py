from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.schemas import LeadOut, LeadStatusUpdate, StatsOut

router = APIRouter(prefix="/api", tags=["leads"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/leads", response_model=list[LeadOut])
def list_leads(
    category: str | None = Query(None, description="'funder' or 'partner'"),
    q: str | None = Query(None, description="Search name, focus area, or subtype"),
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    stmt = select(Lead)

    if category:
        stmt = stmt.where(Lead.category == category)
    if status:
        stmt = stmt.where(Lead.status == status)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Lead.name.ilike(like))
            | (Lead.focus_area.ilike(like))
            | (Lead.subtype.ilike(like))
        )

    stmt = stmt.order_by(Lead.category, Lead.name)
    return db.execute(stmt).scalars().all()


@router.get("/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
    return lead


@router.patch("/leads/{lead_id}", response_model=LeadOut)
def update_lead_status(lead_id: int, body: LeadStatusUpdate, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
    lead.status = body.status
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    total = db.execute(select(func.count()).select_from(Lead)).scalar_one()
    funders = db.execute(
        select(func.count()).select_from(Lead).where(Lead.category == "funder")
    ).scalar_one()
    partners = db.execute(
        select(func.count()).select_from(Lead).where(Lead.category == "partner")
    ).scalar_one()
    status_rows = db.execute(select(Lead.status, func.count()).group_by(Lead.status)).all()

    return StatsOut(
        total=total,
        funders=funders,
        partners=partners,
        by_status={row[0]: row[1] for row in status_rows},
    )
