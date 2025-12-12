"""
Routing API endpoints.
Handles VRP optimization and route management.
"""

import logging
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from db.database import get_db
from db.repositories import (
    PackageRepository,
    AddressRepository,
    VehicleRepository,
    RouteRepository,
)
from models.route import (
    RouteOptimizeRequest,
    RouteOptimizeResponse,
    VehicleRoute as VehicleRouteModel,
    RouteStop as RouteStopModel,
    RouteDetailResponse,
)
from services.vrp_optimizer import (
    get_vrp_optimizer,
    Location,
    Vehicle,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/optimize", response_model=RouteOptimizeResponse)
async def optimize_routes(
    request: RouteOptimizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Optimize delivery routes for a given date.
    
    Uses Google OR-Tools to solve CVRPTW (Capacitated Vehicle Routing
    Problem with Time Windows).
    
    If no packages are specified, uses all geocoded pending packages.
    If no vehicles are specified, uses all active vehicles.
    """
    logger.info(f"Optimizing routes for {request.planned_date}")
    
    vehicle_repo = VehicleRepository(db)
    
    # Get vehicles
    if request.vehicles:
        vehicles_data = []
        for v in request.vehicles:
            vehicles_data.append({
                "id": None,  # Will be looked up
                "vehicle_id": v.vehicle_id,
                "capacity": v.capacity,
                "start_lat": v.start_lat,
                "start_lon": v.start_lon,
                "driver_name": v.driver_name,
            })
    else:
        vehicles_data = await vehicle_repo.get_active()
    
    if not vehicles_data:
        raise HTTPException(
            status_code=400,
            detail="No vehicles available for routing"
        )
    
    # Get packages to route
    if request.package_ids:
        # Get specific packages
        query = text("""
            SELECT 
                p.id as package_id,
                p.package_id as package_code,
                a.id as address_id,
                ST_Y(a.location::geometry) as lat,
                ST_X(a.location::geometry) as lon,
                a.street,
                a.house_number,
                a.subdistrict,
                a.city
            FROM packages p
            JOIN addresses a ON a.package_id = p.id
            WHERE p.package_id = ANY(:package_ids)
            AND a.location IS NOT NULL
            AND p.status IN ('geocoded', 'parsed')
        """)
        result = await db.execute(query, {"package_ids": request.package_ids})
    else:
        # Get all geocoded pending packages
        query = text("""
            SELECT 
                p.id as package_id,
                p.package_id as package_code,
                a.id as address_id,
                ST_Y(a.location::geometry) as lat,
                ST_X(a.location::geometry) as lon,
                a.street,
                a.house_number,
                a.subdistrict,
                a.city
            FROM packages p
            JOIN addresses a ON a.package_id = p.id
            WHERE a.location IS NOT NULL
            AND p.status IN ('geocoded', 'parsed')
            ORDER BY p.created_at
            LIMIT 1000
        """)
        result = await db.execute(query)
    
    packages_data = [dict(row._mapping) for row in result.fetchall()]
    
    if not packages_data:
        return RouteOptimizeResponse(
            success=True,
            planned_date=request.planned_date,
            routes=[],
            unassigned_packages=[],
            total_packages=0,
            total_vehicles_used=0,
            total_distance_km=0,
            optimization_time_ms=0,
            warnings=["No geocoded packages available for routing"]
        )
    
    logger.info(f"Optimizing {len(packages_data)} packages with {len(vehicles_data)} vehicles")
    
    # Build locations list (depot first)
    # Use first vehicle's start location as depot
    depot = Location(
        id="depot",
        lat=vehicles_data[0]["start_lat"],
        lon=vehicles_data[0]["start_lon"],
        demand=0,
        service_time_minutes=0
    )
    
    locations = [depot]
    package_map = {}  # Map location index to package data
    
    for i, pkg in enumerate(packages_data):
        loc = Location(
            id=pkg["package_code"],
            lat=pkg["lat"],
            lon=pkg["lon"],
            demand=1,
            service_time_minutes=5
        )
        locations.append(loc)
        package_map[i + 1] = pkg  # +1 because depot is at index 0
    
    # Build vehicles list
    vehicles = []
    vehicle_map = {}  # Map vehicle index to vehicle data
    
    for i, v in enumerate(vehicles_data):
        vehicle = Vehicle(
            id=v["vehicle_id"],
            capacity=v["capacity"],
            start_location=depot
        )
        vehicles.append(vehicle)
        vehicle_map[i] = v
    
    # Run optimization
    optimizer = get_vrp_optimizer()
    optimizer.max_solve_time = request.max_solve_time_seconds
    
    opt_result = optimizer.optimize(
        locations=locations,
        vehicles=vehicles,
        use_time_windows=request.use_time_windows,
        balance_routes=request.balance_routes
    )
    
    if not opt_result.success:
        return RouteOptimizeResponse(
            success=False,
            planned_date=request.planned_date,
            routes=[],
            unassigned_packages=[p["package_code"] for p in packages_data],
            total_packages=len(packages_data),
            optimization_time_ms=opt_result.solve_time_ms,
            error=opt_result.error
        )
    
    # Convert optimizer result to response model and save to database
    route_repo = RouteRepository(db)
    routes_response = []
    
    for opt_route in opt_result.routes:
        # Find vehicle data
        vehicle_data = next(
            (v for v in vehicles_data if v["vehicle_id"] == opt_route.vehicle_id),
            None
        )
        
        if not vehicle_data:
            continue
        
        # Create route in database
        if vehicle_data.get("id"):
            route_record = await route_repo.create(
                vehicle_id=vehicle_data["id"],
                planned_date=request.planned_date,
                total_distance_km=opt_route.total_distance_km,
                total_time_minutes=opt_route.total_time_minutes,
                total_stops=len(opt_route.stops) - 1,  # Exclude depot
                optimization_time_ms=opt_result.solve_time_ms,
            )
            route_id = route_record["id"]
        else:
            route_id = None
        
        # Build stops response
        stops_response = []
        
        for stop in opt_route.stops:
            if stop.location_id == "depot":
                address_summary = "Depot"
                pkg_data = None
            else:
                # Find package data
                for idx, pkg in package_map.items():
                    if pkg["package_code"] == stop.location_id:
                        pkg_data = pkg
                        break
                else:
                    pkg_data = None
                
                if pkg_data:
                    parts = []
                    if pkg_data.get("street"):
                        parts.append(pkg_data["street"])
                    if pkg_data.get("house_number"):
                        parts.append(pkg_data["house_number"])
                    if pkg_data.get("subdistrict"):
                        parts.append(pkg_data["subdistrict"])
                    address_summary = " ".join(parts) if parts else "Unknown"
                else:
                    address_summary = "Unknown"
            
            stop_model = RouteStopModel(
                sequence=stop.sequence,
                package_id=stop.location_id if stop.location_id != "depot" else None,
                lat=stop.lat,
                lon=stop.lon,
                address_summary=address_summary,
                service_time_minutes=5 if stop.location_id != "depot" else 0,
                cumulative_distance_km=stop.cumulative_distance_km,
                cumulative_time_minutes=stop.cumulative_time_minutes,
            )
            stops_response.append(stop_model)
            
            # Save stop to database
            if route_id and pkg_data and stop.location_id != "depot":
                await route_repo.add_stop(
                    route_id=UUID(route_id),
                    package_id=pkg_data["package_id"],
                    address_id=pkg_data["address_id"],
                    sequence_order=stop.sequence,
                )
        
        route_model = VehicleRouteModel(
            vehicle_id=opt_route.vehicle_id,
            driver_name=vehicle_data.get("driver_name"),
            stops=stops_response,
            total_packages=len([s for s in stops_response if s.package_id]),
            total_distance_km=opt_route.total_distance_km,
            total_time_minutes=opt_route.total_time_minutes,
            load_percentage=opt_route.load_percentage,
        )
        routes_response.append(route_model)
    
    # Update package statuses
    for opt_route in opt_result.routes:
        for stop in opt_route.stops:
            if stop.location_id != "depot":
                for idx, pkg in package_map.items():
                    if pkg["package_code"] == stop.location_id:
                        await db.execute(
                            text("UPDATE packages SET status = 'routed' WHERE id = :id"),
                            {"id": pkg["package_id"]}
                        )
                        break
    
    await db.commit()
    
    return RouteOptimizeResponse(
        success=True,
        planned_date=request.planned_date,
        routes=routes_response,
        unassigned_packages=opt_result.unassigned,
        total_packages=len(packages_data),
        total_vehicles_used=len(routes_response),
        total_distance_km=opt_result.total_distance_km,
        optimization_time_ms=opt_result.solve_time_ms,
        warnings=[]
    )


@router.get("/{route_id}", response_model=RouteDetailResponse)
async def get_route(
    route_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific route."""
    route_repo = RouteRepository(db)
    
    try:
        route_uuid = UUID(route_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid route ID format")
    
    route = await route_repo.get_by_id(route_uuid)
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Convert to response model
    stops = []
    for stop in route.get("stops", []):
        stops.append(RouteStopModel(
            sequence=stop["sequence_order"],
            package_id=stop.get("package_code"),
            lat=stop["lat"],
            lon=stop["lon"],
            address_summary=f"{stop.get('street', '')} {stop.get('house_number', '')}".strip() or "Unknown",
            estimated_arrival=stop.get("estimated_arrival"),
        ))
    
    return RouteDetailResponse(
        route_id=str(route["id"]),
        vehicle_id=route["vehicle_code"],
        driver_name=route.get("driver_name"),
        planned_date=route["planned_date"],
        status=route["status"],
        stops=stops,
        total_distance_km=route.get("total_distance_km", 0),
        total_time_minutes=route.get("total_time_minutes", 0),
        created_at=route["created_at"],
    )


@router.get("/vehicle/{vehicle_id}")
async def get_vehicle_routes(
    vehicle_id: str,
    planned_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get routes for a specific vehicle."""
    vehicle_repo = VehicleRepository(db)
    
    vehicle = await vehicle_repo.get_by_vehicle_id(vehicle_id)
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Query routes
    if planned_date:
        query = text("""
            SELECT r.*, 
                   (SELECT COUNT(*) FROM route_stops WHERE route_id = r.id) as stop_count
            FROM routes r
            WHERE r.vehicle_id = :vehicle_id
            AND r.planned_date = :planned_date
            ORDER BY r.created_at DESC
        """)
        result = await db.execute(query, {
            "vehicle_id": vehicle["id"],
            "planned_date": planned_date
        })
    else:
        query = text("""
            SELECT r.*, 
                   (SELECT COUNT(*) FROM route_stops WHERE route_id = r.id) as stop_count
            FROM routes r
            WHERE r.vehicle_id = :vehicle_id
            ORDER BY r.planned_date DESC, r.created_at DESC
            LIMIT 50
        """)
        result = await db.execute(query, {"vehicle_id": vehicle["id"]})
    
    routes = [dict(row._mapping) for row in result.fetchall()]
    
    return {
        "vehicle": vehicle,
        "routes": routes
    }


@router.get("/")
async def list_routes(
    planned_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List routes with optional filters."""
    conditions = []
    params = {"limit": limit}
    
    if planned_date:
        conditions.append("r.planned_date = :planned_date")
        params["planned_date"] = planned_date
    
    if status:
        conditions.append("r.status = :status")
        params["status"] = status
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = text(f"""
        SELECT 
            r.*,
            v.vehicle_id as vehicle_code,
            v.driver_name,
            (SELECT COUNT(*) FROM route_stops WHERE route_id = r.id) as stop_count
        FROM routes r
        JOIN vehicles v ON v.id = r.vehicle_id
        WHERE {where_clause}
        ORDER BY r.planned_date DESC, r.created_at DESC
        LIMIT :limit
    """)
    
    result = await db.execute(query, params)
    routes = [dict(row._mapping) for row in result.fetchall()]
    
    return {
        "total": len(routes),
        "routes": routes
    }
