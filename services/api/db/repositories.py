"""
Repository pattern for database operations.
Provides async CRUD operations for all entities.
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession


class PackageRepository:
    """Repository for package operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        package_id: str,
        device_id: str,
        ocr_text: str,
        ocr_confidence: float,
        priority: str = "standard",
        operator_id: Optional[str] = None,
        gps_lat: Optional[float] = None,
        gps_lon: Optional[float] = None,
        image_path: Optional[str] = None,
    ) -> dict:
        """Create a new package record."""
        query = text("""
            INSERT INTO packages (
                package_id, device_id, operator_id, ocr_text, 
                ocr_confidence, priority, gps_lat, gps_lon, image_path, status
            ) VALUES (
                :package_id, :device_id, :operator_id, :ocr_text,
                :ocr_confidence, :priority, :gps_lat, :gps_lon, :image_path, 'pending'
            )
            RETURNING id, package_id, status, created_at
        """)
        result = await self.session.execute(query, {
            "package_id": package_id,
            "device_id": device_id,
            "operator_id": operator_id,
            "ocr_text": ocr_text,
            "ocr_confidence": ocr_confidence,
            "priority": priority,
            "gps_lat": gps_lat,
            "gps_lon": gps_lon,
            "image_path": image_path,
        })
        row = result.fetchone()
        return {
            "id": str(row.id),
            "package_id": row.package_id,
            "status": row.status,
            "created_at": row.created_at.isoformat(),
        }
    
    async def get_by_id(self, id: UUID) -> Optional[dict]:
        """Get package by internal UUID."""
        query = text("SELECT * FROM packages WHERE id = :id")
        result = await self.session.execute(query, {"id": id})
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None
    
    async def get_by_package_id(self, package_id: str) -> Optional[dict]:
        """Get package by external package_id."""
        query = text("SELECT * FROM packages WHERE package_id = :package_id")
        result = await self.session.execute(query, {"package_id": package_id})
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None
    
    async def update_status(self, id: UUID, status: str) -> bool:
        """Update package status."""
        query = text("UPDATE packages SET status = :status WHERE id = :id")
        result = await self.session.execute(query, {"id": id, "status": status})
        return result.rowcount > 0
    
    async def get_pending(self, limit: int = 100) -> List[dict]:
        """Get pending packages for processing."""
        query = text("""
            SELECT * FROM packages 
            WHERE status = 'pending' 
            ORDER BY created_at 
            LIMIT :limit
        """)
        result = await self.session.execute(query, {"limit": limit})
        return [dict(row._mapping) for row in result.fetchall()]


class AddressRepository:
    """Repository for address operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        package_id: UUID,
        raw_text: str,
        street: Optional[str] = None,
        house_number: Optional[str] = None,
        rt: Optional[str] = None,
        rw: Optional[str] = None,
        neighborhood: Optional[str] = None,
        subdistrict: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        postal_code: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        geocode_confidence: Optional[float] = None,
        geocode_source: Optional[str] = None,
        requires_verification: bool = False,
    ) -> dict:
        """Create a new address record."""
        # Build location point if coordinates provided
        location_sql = "NULL"
        if lat is not None and lon is not None:
            location_sql = f"ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geography"
        
        query = text(f"""
            INSERT INTO addresses (
                package_id, raw_text, street, house_number, rt, rw,
                neighborhood, subdistrict, city, province, postal_code,
                location, geocode_confidence, geocode_source, requires_verification
            ) VALUES (
                :package_id, :raw_text, :street, :house_number, :rt, :rw,
                :neighborhood, :subdistrict, :city, :province, :postal_code,
                {location_sql}, :geocode_confidence, :geocode_source, :requires_verification
            )
            RETURNING id, package_id, created_at
        """)
        result = await self.session.execute(query, {
            "package_id": package_id,
            "raw_text": raw_text,
            "street": street,
            "house_number": house_number,
            "rt": rt,
            "rw": rw,
            "neighborhood": neighborhood,
            "subdistrict": subdistrict,
            "city": city,
            "province": province,
            "postal_code": postal_code,
            "geocode_confidence": geocode_confidence,
            "geocode_source": geocode_source,
            "requires_verification": requires_verification,
        })
        row = result.fetchone()
        return {
            "id": str(row.id),
            "package_id": str(row.package_id),
            "created_at": row.created_at.isoformat(),
        }
    
    async def get_by_package_id(self, package_id: UUID) -> Optional[dict]:
        """Get address by package ID."""
        query = text("""
            SELECT 
                id, package_id, raw_text, street, house_number, rt, rw,
                neighborhood, subdistrict, city, province, postal_code,
                ST_Y(location::geometry) as lat,
                ST_X(location::geometry) as lon,
                geocode_confidence, geocode_source, requires_verification,
                created_at
            FROM addresses 
            WHERE package_id = :package_id
        """)
        result = await self.session.execute(query, {"package_id": package_id})
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None
    
    async def get_for_routing(self, package_ids: List[UUID]) -> List[dict]:
        """Get addresses with coordinates for routing."""
        query = text("""
            SELECT 
                a.id as address_id,
                a.package_id,
                p.package_id as package_code,
                ST_Y(a.location::geometry) as lat,
                ST_X(a.location::geometry) as lon,
                a.city,
                a.subdistrict
            FROM addresses a
            JOIN packages p ON p.id = a.package_id
            WHERE a.package_id = ANY(:package_ids)
            AND a.location IS NOT NULL
        """)
        result = await self.session.execute(query, {"package_ids": package_ids})
        return [dict(row._mapping) for row in result.fetchall()]


class VehicleRepository:
    """Repository for vehicle operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_active(self) -> List[dict]:
        """Get all active vehicles."""
        query = text("""
            SELECT id, vehicle_id, vehicle_type, capacity, 
                   driver_name, start_lat, start_lon
            FROM vehicles
            WHERE is_active = true
        """)
        result = await self.session.execute(query)
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def get_by_vehicle_id(self, vehicle_id: str) -> Optional[dict]:
        """Get vehicle by external vehicle_id."""
        query = text("SELECT * FROM vehicles WHERE vehicle_id = :vehicle_id")
        result = await self.session.execute(query, {"vehicle_id": vehicle_id})
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None


class RouteRepository:
    """Repository for route operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        vehicle_id: UUID,
        planned_date: date,
        total_distance_km: float,
        total_time_minutes: int,
        total_stops: int,
        optimization_time_ms: int,
    ) -> dict:
        """Create a new route."""
        query = text("""
            INSERT INTO routes (
                vehicle_id, planned_date, total_distance_km,
                total_time_minutes, total_stops, optimization_time_ms, status
            ) VALUES (
                :vehicle_id, :planned_date, :total_distance_km,
                :total_time_minutes, :total_stops, :optimization_time_ms, 'planned'
            )
            RETURNING id, created_at
        """)
        result = await self.session.execute(query, {
            "vehicle_id": vehicle_id,
            "planned_date": planned_date,
            "total_distance_km": total_distance_km,
            "total_time_minutes": total_time_minutes,
            "total_stops": total_stops,
            "optimization_time_ms": optimization_time_ms,
        })
        row = result.fetchone()
        return {
            "id": str(row.id),
            "created_at": row.created_at.isoformat(),
        }
    
    async def add_stop(
        self,
        route_id: UUID,
        package_id: UUID,
        address_id: UUID,
        sequence_order: int,
        estimated_arrival: Optional[str] = None,
    ) -> dict:
        """Add a stop to a route."""
        query = text("""
            INSERT INTO route_stops (
                route_id, package_id, address_id, sequence_order, estimated_arrival
            ) VALUES (
                :route_id, :package_id, :address_id, :sequence_order, :estimated_arrival
            )
            RETURNING id
        """)
        result = await self.session.execute(query, {
            "route_id": route_id,
            "package_id": package_id,
            "address_id": address_id,
            "sequence_order": sequence_order,
            "estimated_arrival": estimated_arrival,
        })
        row = result.fetchone()
        return {"id": str(row.id)}
    
    async def get_by_id(self, route_id: UUID) -> Optional[dict]:
        """Get route with stops."""
        route_query = text("""
            SELECT r.*, v.vehicle_id as vehicle_code, v.driver_name
            FROM routes r
            JOIN vehicles v ON v.id = r.vehicle_id
            WHERE r.id = :route_id
        """)
        route_result = await self.session.execute(route_query, {"route_id": route_id})
        route_row = route_result.fetchone()
        
        if not route_row:
            return None
        
        stops_query = text("""
            SELECT 
                rs.id, rs.sequence_order, rs.estimated_arrival, rs.status,
                p.package_id as package_code,
                a.street, a.house_number, a.city,
                ST_Y(a.location::geometry) as lat,
                ST_X(a.location::geometry) as lon
            FROM route_stops rs
            JOIN packages p ON p.id = rs.package_id
            JOIN addresses a ON a.id = rs.address_id
            WHERE rs.route_id = :route_id
            ORDER BY rs.sequence_order
        """)
        stops_result = await self.session.execute(stops_query, {"route_id": route_id})
        stops = [dict(row._mapping) for row in stops_result.fetchall()]
        
        route = dict(route_row._mapping)
        route["stops"] = stops
        return route
    
    async def get_by_vehicle_and_date(self, vehicle_id: UUID, planned_date: date) -> List[dict]:
        """Get routes for a vehicle on a specific date."""
        query = text("""
            SELECT * FROM routes
            WHERE vehicle_id = :vehicle_id AND planned_date = :planned_date
            ORDER BY created_at
        """)
        result = await self.session.execute(query, {
            "vehicle_id": vehicle_id,
            "planned_date": planned_date,
        })
        return [dict(row._mapping) for row in result.fetchall()]
