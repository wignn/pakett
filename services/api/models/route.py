"""
Pydantic models for routing and VRP optimization.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field


class VehicleInfo(BaseModel):
    """Vehicle information for routing."""
    
    vehicle_id: str = Field(..., description="Vehicle identifier")
    capacity: int = Field(default=50, ge=1, description="Maximum packages")
    start_lat: float = Field(..., description="Start location latitude")
    start_lon: float = Field(..., description="Start location longitude")
    driver_name: Optional[str] = Field(default=None)
    vehicle_type: str = Field(default="motorcycle")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "vehicle_id": "V001",
                    "capacity": 30,
                    "start_lat": -6.2088,
                    "start_lon": 106.8456,
                    "driver_name": "Driver A",
                    "vehicle_type": "motorcycle"
                }
            ]
        }
    }


class PackageLocation(BaseModel):
    """Package with location for routing."""
    
    package_id: str = Field(..., description="Package identifier")
    lat: float = Field(..., description="Delivery latitude")
    lon: float = Field(..., description="Delivery longitude")
    service_time_minutes: int = Field(default=5, ge=1, description="Service time at stop")
    time_window_start: Optional[str] = Field(default=None, description="Earliest delivery time HH:MM")
    time_window_end: Optional[str] = Field(default=None, description="Latest delivery time HH:MM")
    priority: str = Field(default="standard")
    demand: int = Field(default=1, ge=1, description="Capacity units consumed")


class RouteOptimizeRequest(BaseModel):
    """Request to optimize delivery routes."""
    
    planned_date: date = Field(..., description="Date for route planning")
    vehicles: Optional[List[VehicleInfo]] = Field(
        default=None, 
        description="Vehicles to use. If not provided, uses all active vehicles."
    )
    package_ids: Optional[List[str]] = Field(
        default=None,
        description="Package IDs to route. If not provided, uses all geocoded pending packages."
    )
    max_solve_time_seconds: int = Field(default=300, ge=10, le=600)
    
    # Optimization parameters
    use_time_windows: bool = Field(default=False, description="Enforce time windows")
    balance_routes: bool = Field(default=True, description="Balance load across vehicles")
    minimize_distance: bool = Field(default=True, description="Minimize total distance")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "planned_date": "2025-12-12",
                    "max_solve_time_seconds": 120,
                    "balance_routes": True,
                    "minimize_distance": True
                }
            ]
        }
    }


class RouteStop(BaseModel):
    """A stop in a delivery route."""
    
    sequence: int = Field(..., ge=0, description="Stop sequence (0 = depot)")
    package_id: Optional[str] = Field(default=None, description="Package at this stop")
    lat: float = Field(..., description="Stop latitude")
    lon: float = Field(..., description="Stop longitude")
    address_summary: Optional[str] = Field(default=None, description="Short address")
    estimated_arrival: Optional[datetime] = Field(default=None)
    service_time_minutes: int = Field(default=5)
    cumulative_distance_km: float = Field(default=0)
    cumulative_time_minutes: int = Field(default=0)


class VehicleRoute(BaseModel):
    """Optimized route for a single vehicle."""
    
    vehicle_id: str = Field(..., description="Vehicle identifier")
    driver_name: Optional[str] = Field(default=None)
    stops: List[RouteStop] = Field(..., description="Ordered list of stops")
    total_packages: int = Field(..., ge=0)
    total_distance_km: float = Field(..., ge=0)
    total_time_minutes: int = Field(..., ge=0)
    load_percentage: float = Field(..., ge=0, le=100, description="Capacity utilization")


class RouteOptimizeResponse(BaseModel):
    """Response with optimized routes."""
    
    success: bool = Field(..., description="Whether optimization succeeded")
    planned_date: date = Field(..., description="Route date")
    routes: List[VehicleRoute] = Field(default_factory=list, description="Vehicle routes")
    unassigned_packages: List[str] = Field(default_factory=list, description="Packages that couldn't be routed")
    
    # Optimization metadata
    total_packages: int = Field(default=0)
    total_vehicles_used: int = Field(default=0)
    total_distance_km: float = Field(default=0)
    optimization_time_ms: int = Field(default=0, description="Solve time in milliseconds")
    
    # Warnings/info
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = Field(default=None)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "planned_date": "2025-12-12",
                    "routes": [
                        {
                            "vehicle_id": "V001",
                            "driver_name": "Driver A",
                            "stops": [
                                {"sequence": 0, "lat": -6.2088, "lon": 106.8456, "address_summary": "Depot"},
                                {"sequence": 1, "package_id": "PKT001", "lat": -6.225, "lon": 106.795, "address_summary": "Jalan Merdeka 45"}
                            ],
                            "total_packages": 15,
                            "total_distance_km": 25.4,
                            "total_time_minutes": 180,
                            "load_percentage": 50.0
                        }
                    ],
                    "unassigned_packages": [],
                    "total_packages": 30,
                    "total_vehicles_used": 2,
                    "total_distance_km": 47.5,
                    "optimization_time_ms": 1250
                }
            ]
        }
    }


class RouteDetailResponse(BaseModel):
    """Detailed route information."""
    
    route_id: str = Field(..., description="Route UUID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    driver_name: Optional[str] = Field(default=None)
    planned_date: date = Field(...)
    status: str = Field(default="planned")
    stops: List[RouteStop] = Field(default_factory=list)
    total_distance_km: float = Field(default=0)
    total_time_minutes: int = Field(default=0)
    created_at: datetime = Field(...)
