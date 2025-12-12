// API Types

export interface Package {
    id: string;
    package_id: string;
    device_id: string;
    ocr_text: string;
    ocr_confidence: number;
    status: PackageStatus;
    priority: string;
    created_at: string;
    address?: Address;
}

export type PackageStatus =
    | 'pending'
    | 'processing'
    | 'parsed'
    | 'geocoded'
    | 'routed'
    | 'delivered'
    | 'failed'
    | 'verification_needed';

export interface Address {
    id: string;
    raw_text: string;
    street?: string;
    house_number?: string;
    rt?: string;
    rw?: string;
    neighborhood?: string;
    subdistrict?: string;
    city?: string;
    province?: string;
    postal_code?: string;
    lat?: number;
    lon?: number;
    geocode_confidence?: number;
    requires_verification: boolean;
}

export interface Vehicle {
    id: string;
    vehicle_id: string;
    vehicle_type: string;
    capacity: number;
    driver_name?: string;
    start_lat: number;
    start_lon: number;
    is_active: boolean;
}

export interface Route {
    id: string;
    vehicle_id: string;
    vehicle_code?: string;
    driver_name?: string;
    planned_date: string;
    status: string;
    total_distance_km: number;
    total_time_minutes: number;
    total_stops: number;
    stops?: RouteStop[];
}

export interface RouteStop {
    id?: string;
    sequence: number;
    package_id?: string;
    lat: number;
    lon: number;
    address_summary?: string;
    estimated_arrival?: string;
    actual_arrival?: string;
    status: string;
}

export interface Stats {
    total_packages: number;
    pending_packages: number;
    geocoded_packages: number;
    routed_packages: number;
    verification_needed: number;
    total_routes_today: number;
    active_vehicles: number;
    avg_confidence: number;
}

export interface OptimizeRequest {
    planned_date: string;
    max_solve_time_seconds?: number;
    balance_routes?: boolean;
}

export interface OptimizeResponse {
    success: boolean;
    planned_date: string;
    routes: RouteResult[];
    unassigned_packages: string[];
    total_packages: number;
    total_vehicles_used: number;
    total_distance_km: number;
    optimization_time_ms: number;
    warnings: string[];
    error?: string;
}

export interface RouteResult {
    vehicle_id: string;
    driver_name?: string;
    stops: RouteStop[];
    total_packages: number;
    total_distance_km: number;
    total_time_minutes: number;
    load_percentage: number;
}

export interface ParsedAddress {
    raw_text: string;
    street?: string;
    house_number?: string;
    rt?: string;
    rw?: string;
    neighborhood?: string;
    subdistrict?: string;
    city?: string;
    province?: string;
    postal_code?: string;
    confidence: number;
    corrections_applied: string[];
}
