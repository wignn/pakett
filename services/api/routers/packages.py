"""
Packages API endpoints.
Handles package listing and management for driver app.
"""

import logging
from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from db.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_packages(
    status: Optional[str] = Query(None, description="Filter by status: pending, parsed, geocoded, routed, delivered"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List packages with optional status filter.
    
    Returns packages that can be viewed by driver app.
    """
    conditions = ["1=1"]
    params = {"limit": limit, "offset": offset}
    
    if status:
        conditions.append("p.status = :status")
        params["status"] = status
    
    where_clause = " AND ".join(conditions)
    
    query = text(f"""
        SELECT 
            p.id,
            p.package_id,
            p.status,
            p.priority,
            p.ocr_confidence,
            p.created_at,
            a.street,
            a.house_number,
            a.subdistrict,
            a.city,
            a.province,
            a.postal_code,
            ST_Y(a.location::geometry) as lat,
            ST_X(a.location::geometry) as lon,
            a.geocode_confidence
        FROM packages p
        LEFT JOIN addresses a ON a.package_id = p.id
        WHERE {where_clause}
        ORDER BY p.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    
    result = await db.execute(query, params)
    packages = []
    
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        # Format address summary
        address_parts = []
        if row_dict.get("street"):
            address_parts.append(row_dict["street"])
        if row_dict.get("house_number"):
            address_parts.append(row_dict["house_number"])
        if row_dict.get("subdistrict"):
            address_parts.append(row_dict["subdistrict"])
        if row_dict.get("city"):
            address_parts.append(row_dict["city"])
        
        row_dict["address_summary"] = ", ".join(address_parts) if address_parts else None
        packages.append(row_dict)
    
    # Get total count
    count_query = text(f"SELECT COUNT(*) FROM packages p WHERE {where_clause}")
    count_result = await db.execute(count_query, params)
    total = count_result.scalar()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "packages": packages
    }


@router.get("/ready-for-delivery")
async def get_packages_ready_for_delivery(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Get packages that are geocoded and ready for delivery.
    These are packages that haven't been assigned to a route yet.
    """
    query = text("""
        SELECT 
            p.id,
            p.package_id,
            p.status,
            p.priority,
            p.created_at,
            a.street,
            a.house_number,
            a.subdistrict,
            a.city,
            a.raw_text,
            ST_Y(a.location::geometry) as lat,
            ST_X(a.location::geometry) as lon
        FROM packages p
        LEFT JOIN addresses a ON a.package_id = p.id
        WHERE p.status IN ('geocoded', 'parsed', 'pending', 'verification_needed')
        ORDER BY 
            CASE p.priority 
                WHEN 'express' THEN 1 
                WHEN 'standard' THEN 2 
                ELSE 3 
            END,
            p.created_at ASC
        LIMIT :limit
    """)
    
    result = await db.execute(query, {"limit": limit})
    packages = []
    
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        address_parts = []
        if row_dict.get("street"):
            address_parts.append(row_dict["street"])
        if row_dict.get("house_number"):
            address_parts.append(row_dict["house_number"])
        if row_dict.get("subdistrict"):
            address_parts.append(row_dict["subdistrict"])
        if row_dict.get("city"):
            address_parts.append(row_dict["city"])
        
        # Use raw_text as fallback if no parsed address
        if address_parts:
            row_dict["address_summary"] = ", ".join(address_parts)
        elif row_dict.get("raw_text"):
            # Take first line of raw text as summary
            raw_lines = row_dict["raw_text"].split('\n')
            row_dict["address_summary"] = raw_lines[0][:50] if raw_lines else "No address"
        else:
            row_dict["address_summary"] = "No address"
        
        packages.append(row_dict)
    
    return {
        "total": len(packages),
        "packages": packages
    }


@router.get("/stats")
async def get_package_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get package statistics by status."""
    query = text("""
        SELECT 
            status,
            COUNT(*) as count
        FROM packages
        GROUP BY status
    """)
    
    result = await db.execute(query)
    stats = {row.status: row.count for row in result.fetchall()}
    
    return {
        "stats": stats,
        "total": sum(stats.values())
    }


@router.get("/{package_id}")
async def get_package(
    package_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed package information."""
    query = text("""
        SELECT 
            p.*,
            a.street,
            a.house_number,
            a.rt,
            a.rw,
            a.neighborhood,
            a.subdistrict,
            a.city,
            a.province,
            a.postal_code,
            ST_Y(a.location::geometry) as lat,
            ST_X(a.location::geometry) as lon,
            a.geocode_confidence
        FROM packages p
        LEFT JOIN addresses a ON a.package_id = p.id
        WHERE p.package_id = :package_id
    """)
    
    result = await db.execute(query, {"package_id": package_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return dict(row._mapping)


@router.patch("/{package_id}/status")
async def update_package_status(
    package_id: str,
    status: str = Query(..., description="New status"),
    db: AsyncSession = Depends(get_db)
):
    """Update package delivery status."""
    valid_statuses = ['pending', 'parsed', 'geocoded', 'routed', 'in_transit', 'delivered', 'failed']
    
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    query = text("""
        UPDATE packages 
        SET status = :status, updated_at = NOW()
        WHERE package_id = :package_id
        RETURNING id, package_id, status
    """)
    
    result = await db.execute(query, {"package_id": package_id, "status": status})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Package not found")
    
    await db.commit()
    
    return {
        "success": True,
        "package_id": row.package_id,
        "status": row.status
    }
