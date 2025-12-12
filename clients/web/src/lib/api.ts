// API Client functions

import { Package, Stats, Route, OptimizeRequest, OptimizeResponse, ParsedAddress } from './types';

const API_BASE = '/api/v1';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

// Packages
export async function fetchPackages(limit = 50): Promise<Package[]> {
    try {
        const data = await fetchAPI<{ packages: Package[] }>(`/ingest?limit=${limit}`);
        return data.packages || [];
    } catch {
        // Return mock data for demo
        return generateMockPackages(limit);
    }
}

export async function fetchPackage(packageId: string): Promise<Package> {
    return fetchAPI<Package>(`/ingest/${packageId}`);
}

export async function ingestPackage(data: {
    device_id: string;
    package_id: string;
    ocr_text: string;
    ocr_confidence: number;
    priority?: string;
}): Promise<Package> {
    return fetchAPI<Package>('/ingest/ocr-text', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

// Address
export async function parseAddress(rawText: string): Promise<ParsedAddress> {
    const response = await fetchAPI<{ success: boolean; address: ParsedAddress }>(
        '/address/parse',
        {
            method: 'POST',
            body: JSON.stringify({ raw_text: rawText, apply_corrections: true }),
        }
    );
    return response.address;
}

export async function geocodeAddress(address: Partial<ParsedAddress>): Promise<{
    success: boolean;
    location?: { lat: number; lon: number; confidence: number };
}> {
    return fetchAPI('/address/geocode', {
        method: 'POST',
        body: JSON.stringify({ address, use_cache: true }),
    });
}

// Routes
export async function fetchRoutes(date?: string): Promise<Route[]> {
    try {
        const params = date ? `?planned_date=${date}` : '';
        const data = await fetchAPI<{ routes: Route[] }>(`/routes${params}`);
        return data.routes || [];
    } catch {
        return generateMockRoutes();
    }
}

export async function fetchRoute(routeId: string): Promise<Route> {
    return fetchAPI<Route>(`/routes/${routeId}`);
}

export async function optimizeRoutes(request: OptimizeRequest): Promise<OptimizeResponse> {
    return fetchAPI<OptimizeResponse>('/routes/optimize', {
        method: 'POST',
        body: JSON.stringify(request),
    });
}

// Stats
export async function fetchStats(): Promise<Stats> {
    try {
        // Try to get real stats from health endpoint
        await fetchAPI('/health/ready');

        // Aggregate stats from packages
        const packages = await fetchPackages(200);

        return {
            total_packages: packages.length,
            pending_packages: packages.filter(p => p.status === 'pending').length,
            geocoded_packages: packages.filter(p => p.status === 'geocoded').length,
            routed_packages: packages.filter(p => p.status === 'routed').length,
            verification_needed: packages.filter(p => p.status === 'verification_needed').length,
            total_routes_today: 0,
            active_vehicles: 3,
            avg_confidence: packages.reduce((sum, p) => sum + p.ocr_confidence, 0) / packages.length || 0,
        };
    } catch {
        // Return mock stats for demo
        return {
            total_packages: 156,
            pending_packages: 12,
            geocoded_packages: 89,
            routed_packages: 45,
            verification_needed: 10,
            total_routes_today: 8,
            active_vehicles: 5,
            avg_confidence: 0.87,
        };
    }
}

// Mock data generators for demo
function generateMockPackages(count: number): Package[] {
    const statuses = ['pending', 'geocoded', 'routed', 'verification_needed'] as const;
    const cities = ['Jakarta Selatan', 'Jakarta Pusat', 'Jakarta Barat', 'Jakarta Timur', 'Jakarta Utara'];
    const streets = ['Jalan Sudirman', 'Jalan Thamrin', 'Jalan Gatot Subroto', 'Jalan Rasuna Said', 'Jalan Kemang'];

    return Array.from({ length: count }, (_, i) => {
        const status = statuses[Math.floor(Math.random() * statuses.length)];
        const city = cities[Math.floor(Math.random() * cities.length)];
        const street = streets[Math.floor(Math.random() * streets.length)];
        const num = Math.floor(Math.random() * 200) + 1;

        return {
            id: `pkg-${i + 1}`,
            package_id: `PKT${new Date().getFullYear()}${String(i + 1).padStart(6, '0')}`,
            device_id: `scanner-${Math.floor(Math.random() * 20) + 1}`,
            ocr_text: `${street} No. ${num}, RT 0${Math.floor(Math.random() * 9) + 1}/RW 0${Math.floor(Math.random() * 9) + 1}, ${city}`,
            ocr_confidence: Math.random() * 0.3 + 0.65,
            status,
            priority: Math.random() > 0.8 ? 'high' : 'standard',
            created_at: new Date(Date.now() - Math.random() * 86400000).toISOString(),
        };
    });
}

function generateMockRoutes(): Route[] {
    return [
        {
            id: 'route-1',
            vehicle_id: 'V001',
            vehicle_code: 'V001',
            driver_name: 'Driver A',
            planned_date: new Date().toISOString().split('T')[0],
            status: 'planned',
            total_distance_km: 25.4,
            total_time_minutes: 180,
            total_stops: 12,
            stops: [
                { sequence: 0, lat: -6.2088, lon: 106.8456, address_summary: 'Depot', status: 'completed' },
                { sequence: 1, package_id: 'PKT001', lat: -6.225, lon: 106.795, address_summary: 'Jalan Sudirman 45', status: 'pending' },
                { sequence: 2, package_id: 'PKT002', lat: -6.235, lon: 106.780, address_summary: 'Jalan Thamrin 12', status: 'pending' },
                { sequence: 3, package_id: 'PKT003', lat: -6.215, lon: 106.820, address_summary: 'Jalan Gatot Subroto 78', status: 'pending' },
            ],
        },
        {
            id: 'route-2',
            vehicle_id: 'V002',
            vehicle_code: 'V002',
            driver_name: 'Driver B',
            planned_date: new Date().toISOString().split('T')[0],
            status: 'planned',
            total_distance_km: 18.7,
            total_time_minutes: 150,
            total_stops: 8,
            stops: [
                { sequence: 0, lat: -6.2088, lon: 106.8456, address_summary: 'Depot', status: 'completed' },
                { sequence: 1, package_id: 'PKT004', lat: -6.180, lon: 106.830, address_summary: 'Jalan Kemang 33', status: 'pending' },
                { sequence: 2, package_id: 'PKT005', lat: -6.190, lon: 106.850, address_summary: 'Jalan Rasuna Said 99', status: 'pending' },
            ],
        },
    ];
}
