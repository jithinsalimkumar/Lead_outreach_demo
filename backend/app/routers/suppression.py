"""
Suppression list router — view, add, and remove suppressed emails/domains.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.suppression import Suppression
from app.models.user import User
from app.schemas.suppression import SuppressionCreate, SuppressionOut

router = APIRouter(prefix="/api/suppression", tags=["suppression"])


@router.get("", response_model=dict)
async def list_suppression(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Search by email or domain"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List suppression entries with optional search and pagination."""
    query = select(Suppression)
    count_query = select(func.count(Suppression.id))

    # Apply search filter (case-insensitive partial match)
    if search:
        query = query.where(Suppression.email_or_domain.ilike(f"%{search}%"))
        count_query = count_query.where(Suppression.email_or_domain.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Suppression.created_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return {
        "items": [SuppressionOut.model_validate(s) for s in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.post("", response_model=SuppressionOut, status_code=status.HTTP_201_CREATED)
async def add_suppression(
    body: SuppressionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new entry to the suppression list."""
    # Check for duplicate
    existing = await db.execute(
        select(Suppression).where(Suppression.email_or_domain == body.email_or_domain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email/domain is already suppressed",
        )

    # Validate reason
    valid_reasons = {"bounced", "complained", "unsubscribed", "manual"}
    if body.reason not in valid_reasons:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reason. Must be one of: {', '.join(valid_reasons)}",
        )

    entry = Suppression(
        email_or_domain=body.email_or_domain,
        reason=body.reason,
        country=body.country,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/{entry_id}")
async def remove_suppression(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove an entry from the suppression list."""
    result = await db.execute(select(Suppression).where(Suppression.id == entry_id))
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Suppression entry not found")

    await db.delete(entry)
    await db.commit()
    return {"message": "Suppression entry removed"}
