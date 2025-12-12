"""
VRP Optimizer Service.
Solves Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)
using Google OR-Tools.
"""

import math
import logging
import time
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class Location:
    """A location with coordinates."""
    id: str
    lat: float
    lon: float
    demand: int = 1
    service_time_minutes: int = 5
    time_window_start: Optional[int] = None  # Minutes from start of day
    time_window_end: Optional[int] = None


@dataclass
class Vehicle:
    """A vehicle for routing."""
    id: str
    capacity: int
    start_location: Location
    end_location: Optional[Location] = None  # If None, returns to start


@dataclass
class RouteStop:
    """A stop in a route."""
    location_id: str
    sequence: int
    lat: float
    lon: float
    arrival_time_minutes: int
    departure_time_minutes: int
    cumulative_distance_km: float
    cumulative_time_minutes: int


@dataclass
class VehicleRoute:
    """Optimized route for a vehicle."""
    vehicle_id: str
    stops: List[RouteStop]
    total_distance_km: float
    total_time_minutes: int
    total_demand: int
    load_percentage: float


@dataclass
class OptimizationResult:
    """Result of route optimization."""
    success: bool
    routes: List[VehicleRoute] = field(default_factory=list)
    unassigned: List[str] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_time_minutes: int = 0
    solve_time_ms: int = 0
    error: Optional[str] = None


class VRPOptimizer:
    """
    Vehicle Routing Problem optimizer using OR-Tools.
    
    Solves CVRPTW (Capacitated VRP with Time Windows):
    - Capacity constraints per vehicle
    - Time window constraints per delivery
    - Service time at each stop
    - Minimizes total distance
    """
    
    def __init__(self):
        """Initialize VRP optimizer."""
        self.max_solve_time = settings.vrp_max_solve_time_seconds
        self.default_service_time = settings.vrp_default_service_time_minutes
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def create_distance_matrix(self, locations: List[Location]) -> List[List[int]]:
        """
        Create distance matrix for all locations.
        
        Returns distances in meters (integers for OR-Tools).
        """
        n = len(locations)
        matrix = [[0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist_km = self.haversine_distance(
                        locations[i].lat, locations[i].lon,
                        locations[j].lat, locations[j].lon
                    )
                    # Convert to meters and round to integer
                    matrix[i][j] = int(dist_km * 1000)
        
        return matrix
    
    def create_time_matrix(
        self,
        distance_matrix: List[List[int]],
        avg_speed_kmh: float = 30.0
    ) -> List[List[int]]:
        """
        Create time matrix based on distance and average speed.
        
        Returns travel times in minutes.
        """
        n = len(distance_matrix)
        time_matrix = [[0] * n for _ in range(n)]
        
        # Convert speed to m/min
        speed_m_per_min = (avg_speed_kmh * 1000) / 60
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Time in minutes
                    time_minutes = distance_matrix[i][j] / speed_m_per_min
                    time_matrix[i][j] = int(time_minutes)
        
        return time_matrix
    
    def optimize(
        self,
        locations: List[Location],
        vehicles: List[Vehicle],
        use_time_windows: bool = False,
        balance_routes: bool = True,
        avg_speed_kmh: float = 30.0
    ) -> OptimizationResult:
        """
        Optimize vehicle routes for given locations.
        
        Args:
            locations: List of delivery locations (first is depot)
            vehicles: List of vehicles
            use_time_windows: Whether to enforce time windows
            balance_routes: Whether to balance load across vehicles
            avg_speed_kmh: Average vehicle speed
            
        Returns:
            OptimizationResult with optimized routes
        """
        start_time = time.time()
        
        if not locations or not vehicles:
            return OptimizationResult(
                success=False,
                error="No locations or vehicles provided"
            )
        
        num_locations = len(locations)
        num_vehicles = len(vehicles)
        
        logger.info(f"Optimizing routes for {num_locations} locations with {num_vehicles} vehicles")
        
        # Create the data model
        distance_matrix = self.create_distance_matrix(locations)
        time_matrix = self.create_time_matrix(distance_matrix, avg_speed_kmh)
        
        # Create routing index manager
        # All vehicles start and end at index 0 (depot)
        manager = pywrapcp.RoutingIndexManager(
            num_locations,
            num_vehicles,
            0  # Depot index
        )
        
        # Create routing model
        routing = pywrapcp.RoutingModel(manager)
        
        # Distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add distance dimension
        routing.AddDimension(
            transit_callback_index,
            0,  # No slack
            100000000,  # Maximum distance per vehicle (100km in meters)
            True,  # Start cumul at zero
            'Distance'
        )
        distance_dimension = routing.GetDimensionOrDie('Distance')
        
        # Add capacity constraints
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            if from_node == 0:  # Depot has no demand
                return 0
            return locations[from_node].demand
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        vehicle_capacities = [v.capacity for v in vehicles]
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # No slack
            vehicle_capacities,
            True,  # Start cumul at zero
            'Capacity'
        )
        
        # Add time dimension for time windows
        if use_time_windows:
            def time_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                travel_time = time_matrix[from_node][to_node]
                service_time = locations[from_node].service_time_minutes if from_node != 0 else 0
                return travel_time + service_time
            
            time_callback_index = routing.RegisterTransitCallback(time_callback)
            
            routing.AddDimension(
                time_callback_index,
                30,  # Allow 30 min slack for waiting
                1440,  # Maximum time per vehicle (24 hours in minutes)
                False,  # Don't force start cumul to zero
                'Time'
            )
            time_dimension = routing.GetDimensionOrDie('Time')
            
            # Apply time windows
            for location_idx, location in enumerate(locations):
                if location_idx == 0:  # Skip depot
                    continue
                
                index = manager.NodeToIndex(location_idx)
                
                if location.time_window_start is not None and location.time_window_end is not None:
                    time_dimension.CumulVar(index).SetRange(
                        location.time_window_start,
                        location.time_window_end
                    )
        
        # Balance routes if requested
        if balance_routes:
            distance_dimension.SetGlobalSpanCostCoefficient(100)
        
        # Allow dropping nodes if necessary (with high penalty)
        penalty = 100000
        for node in range(1, num_locations):
            routing.AddDisjunction([manager.NodeToIndex(node)], penalty)
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = self.max_solve_time
        search_parameters.log_search = settings.debug
        
        # Solve
        solution = routing.SolveWithParameters(search_parameters)
        
        solve_time_ms = int((time.time() - start_time) * 1000)
        
        if not solution:
            logger.warning("No solution found for VRP")
            return OptimizationResult(
                success=False,
                error="No feasible solution found",
                solve_time_ms=solve_time_ms
            )
        
        # Extract solution
        routes = []
        unassigned = []
        total_distance = 0
        total_time = 0
        
        for vehicle_idx in range(num_vehicles):
            index = routing.Start(vehicle_idx)
            stops = []
            route_distance = 0
            route_time = 0
            route_demand = 0
            sequence = 0
            
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                
                # Get cumulative values
                distance_var = distance_dimension.CumulVar(index)
                cumulative_distance_m = solution.Value(distance_var)
                
                location = locations[node]
                
                stops.append(RouteStop(
                    location_id=location.id,
                    sequence=sequence,
                    lat=location.lat,
                    lon=location.lon,
                    arrival_time_minutes=route_time,
                    departure_time_minutes=route_time + location.service_time_minutes,
                    cumulative_distance_km=cumulative_distance_m / 1000,
                    cumulative_time_minutes=route_time
                ))
                
                if node != 0:  # Not depot
                    route_demand += location.demand
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_idx
                )
                route_time += time_matrix[manager.IndexToNode(previous_index)][manager.IndexToNode(index)]
                sequence += 1
            
            # Skip empty routes (only depot)
            if len(stops) > 1:
                vehicle = vehicles[vehicle_idx]
                route_distance_km = route_distance / 1000
                
                routes.append(VehicleRoute(
                    vehicle_id=vehicle.id,
                    stops=stops,
                    total_distance_km=route_distance_km,
                    total_time_minutes=route_time,
                    total_demand=route_demand,
                    load_percentage=(route_demand / vehicle.capacity) * 100 if vehicle.capacity > 0 else 0
                ))
                
                total_distance += route_distance_km
                total_time += route_time
        
        # Find unassigned locations
        for node in range(1, num_locations):
            index = manager.NodeToIndex(node)
            if solution.Value(routing.NextVar(index)) == index:
                unassigned.append(locations[node].id)
        
        logger.info(
            f"Optimization completed: {len(routes)} routes, "
            f"{len(unassigned)} unassigned, {solve_time_ms}ms"
        )
        
        return OptimizationResult(
            success=True,
            routes=routes,
            unassigned=unassigned,
            total_distance_km=total_distance,
            total_time_minutes=total_time,
            solve_time_ms=solve_time_ms
        )


# Singleton instance
_optimizer_instance: Optional[VRPOptimizer] = None


def get_vrp_optimizer() -> VRPOptimizer:
    """Get singleton VRP optimizer instance."""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = VRPOptimizer()
    return _optimizer_instance
