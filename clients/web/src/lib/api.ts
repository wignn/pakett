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
    const data = await fetchAPI<{ packages: Package[] }>(`/packages/?limit=${limit}`);
    return data.packages || [];
}

export async function fetchPackage(packageId: string): Promise<Package> {
    return fetchAPI<Package>(`/packages/${packageId}`);
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
    const params = date ? `?planned_date=${date}` : '';
    const data = await fetchAPI<{ routes: Route[] }>(`/routes/${params}`);
    return data.routes || [];
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
    // Get stats from packages endpoint
    const statsData = await fetchAPI<{ stats: Record<string, number>; total: number }>('/packages/stats');
    const packages = await fetchPackages(200);

    return {
        total_packages: statsData.total || 0,
        pending_packages: statsData.stats?.pending || 0,
        geocoded_packages: statsData.stats?.geocoded || 0,
        routed_packages: statsData.stats?.routed || 0,
        verification_needed: statsData.stats?.verification_needed || 0,
        total_routes_today: 0,
        active_vehicles: 3,
        avg_confidence: packages.length > 0
            ? packages.reduce((sum, p) => sum + (p.ocr_confidence || 0), 0) / packages.length
            : 0,
    };
}


