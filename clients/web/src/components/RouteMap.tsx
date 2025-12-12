'use client';

import { useEffect, useState } from 'react';
import { Route } from '@/lib/types';
import dynamic from 'next/dynamic';

// Dynamic import to avoid SSR issues with Leaflet
const MapContainer = dynamic(
    () => import('react-leaflet').then((mod) => mod.MapContainer),
    { ssr: false }
);
const TileLayer = dynamic(
    () => import('react-leaflet').then((mod) => mod.TileLayer),
    { ssr: false }
);
const Marker = dynamic(
    () => import('react-leaflet').then((mod) => mod.Marker),
    { ssr: false }
);
const Popup = dynamic(
    () => import('react-leaflet').then((mod) => mod.Popup),
    { ssr: false }
);
const Polyline = dynamic(
    () => import('react-leaflet').then((mod) => mod.Polyline),
    { ssr: false }
);

interface RouteMapProps {
    routes: Route[];
    height?: number;
}

// Route colors
const ROUTE_COLORS = ['#3b82f6', '#22c55e', '#f97316', '#a855f7', '#ec4899'];

export default function RouteMap({ routes, height = 400 }: RouteMapProps) {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return (
            <div
                className="map-container"
                style={{
                    height,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'var(--bg-tertiary)'
                }}
            >
                <p style={{ color: 'var(--text-muted)' }}>Loading map...</p>
            </div>
        );
    }

    // Jakarta center
    const center: [number, number] = [-6.2088, 106.8456];

    return (
        <div className="map-container" style={{ height }}>
            <link
                rel="stylesheet"
                href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
                crossOrigin=""
            />
            <MapContainer
                center={center}
                zoom={12}
                style={{ height: '100%', width: '100%' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {routes.map((route, routeIndex) => {
                    const color = ROUTE_COLORS[routeIndex % ROUTE_COLORS.length];
                    const stops = route.stops || [];

                    // Create polyline from stops
                    const positions: [number, number][] = stops.map(stop => [stop.lat, stop.lon]);

                    return (
                        <div key={route.id}>
                            {/* Route line */}
                            {positions.length > 1 && (
                                <Polyline
                                    positions={positions}
                                    pathOptions={{
                                        color,
                                        weight: 4,
                                        opacity: 0.8,
                                        dashArray: '10, 5'
                                    }}
                                />
                            )}

                            {/* Stop markers */}
                            {stops.map((stop, stopIndex) => (
                                <Marker
                                    key={`${route.id}-${stopIndex}`}
                                    position={[stop.lat, stop.lon]}
                                >
                                    <Popup>
                                        <div style={{ minWidth: '150px' }}>
                                            <strong style={{ color: color }}>
                                                {route.vehicle_code || route.vehicle_id}
                                            </strong>
                                            <p style={{ margin: '4px 0' }}>
                                                Stop #{stop.sequence}: {stop.address_summary || 'Unknown'}
                                            </p>
                                            {stop.package_id && (
                                                <p style={{ fontSize: '12px', color: '#666' }}>
                                                    Package: {stop.package_id}
                                                </p>
                                            )}
                                        </div>
                                    </Popup>
                                </Marker>
                            ))}
                        </div>
                    );
                })}
            </MapContainer>
        </div>
    );
}
