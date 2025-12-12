'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import RouteMap from '@/components/RouteMap';
import { Route, OptimizeResponse } from '@/lib/types';
import { fetchRoutes, optimizeRoutes } from '@/lib/api';
import { Play, RefreshCw, Truck, MapPin, Clock, Route as RouteIcon } from 'lucide-react';

export default function RoutesPage() {
    const [routes, setRoutes] = useState<Route[]>([]);
    const [loading, setLoading] = useState(true);
    const [optimizing, setOptimizing] = useState(false);
    const [optimizeResult, setOptimizeResult] = useState<OptimizeResponse | null>(null);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

    useEffect(() => {
        loadRoutes();
    }, [selectedDate]);

    async function loadRoutes() {
        try {
            setLoading(true);
            const data = await fetchRoutes(selectedDate);
            setRoutes(data);
        } catch (error) {
            console.error('Failed to load routes:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleOptimize() {
        try {
            setOptimizing(true);
            const result = await optimizeRoutes({
                planned_date: selectedDate,
                max_solve_time_seconds: 120,
                balance_routes: true,
            });
            setOptimizeResult(result);
            await loadRoutes();
        } catch (error) {
            console.error('Optimization failed:', error);
        } finally {
            setOptimizing(false);
        }
    }

    // Calculate totals
    const totalDistance = routes.reduce((sum, r) => sum + r.total_distance_km, 0);
    const totalTime = routes.reduce((sum, r) => sum + r.total_time_minutes, 0);
    const totalStops = routes.reduce((sum, r) => sum + r.total_stops, 0);

    return (
        <div className="layout">
            <Sidebar active="routes" />

            <main className="main-content">
                <div className="page-header">
                    <h1 className="page-title">Route Optimization</h1>
                    <p className="page-description">
                        Optimize and manage delivery routes using VRP algorithms
                    </p>
                </div>

                {/* Actions Bar */}
                <div className="card" style={{ marginBottom: '24px' }}>
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label className="input-label">Planned Date</label>
                            <input
                                type="date"
                                className="input"
                                value={selectedDate}
                                onChange={(e) => setSelectedDate(e.target.value)}
                                style={{ width: '180px' }}
                            />
                        </div>

                        <div style={{ flex: 1 }} />

                        <button className="btn btn-secondary" onClick={loadRoutes} disabled={loading}>
                            <RefreshCw size={16} className={loading ? 'loading' : ''} />
                            Refresh
                        </button>
                        <button className="btn btn-primary" onClick={handleOptimize} disabled={optimizing}>
                            <Play size={16} />
                            {optimizing ? 'Optimizing...' : 'Run Optimization'}
                        </button>
                    </div>
                </div>

                {/* Optimization Result */}
                {optimizeResult && (
                    <div className="card" style={{
                        marginBottom: '24px',
                        background: optimizeResult.success
                            ? 'rgba(34, 197, 94, 0.1)'
                            : 'rgba(239, 68, 68, 0.1)',
                        borderColor: optimizeResult.success
                            ? 'var(--accent-green)'
                            : 'var(--accent-red)'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <div style={{
                                width: '48px',
                                height: '48px',
                                borderRadius: '50%',
                                background: optimizeResult.success ? 'var(--accent-green)' : 'var(--accent-red)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}>
                                <RouteIcon size={24} color="white" />
                            </div>
                            <div>
                                <h3 style={{ margin: 0 }}>
                                    {optimizeResult.success ? 'Optimization Complete!' : 'Optimization Failed'}
                                </h3>
                                <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)' }}>
                                    {optimizeResult.success
                                        ? `Created ${optimizeResult.total_vehicles_used} routes for ${optimizeResult.total_packages} packages in ${optimizeResult.optimization_time_ms}ms`
                                        : optimizeResult.error
                                    }
                                </p>
                            </div>
                            <button
                                className="btn btn-secondary btn-sm"
                                style={{ marginLeft: 'auto' }}
                                onClick={() => setOptimizeResult(null)}
                            >
                                Dismiss
                            </button>
                        </div>
                    </div>
                )}

                {/* Stats */}
                <div className="stats-grid" style={{ marginBottom: '24px' }}>
                    <div className="stat-card">
                        <div className="stat-icon purple">
                            <Truck size={24} />
                        </div>
                        <div>
                            <div className="stat-value">{routes.length}</div>
                            <div className="stat-label">Active Routes</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon blue">
                            <MapPin size={24} />
                        </div>
                        <div>
                            <div className="stat-value">{totalStops}</div>
                            <div className="stat-label">Total Stops</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon green">
                            <RouteIcon size={24} />
                        </div>
                        <div>
                            <div className="stat-value">{totalDistance.toFixed(1)} km</div>
                            <div className="stat-label">Total Distance</div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-icon orange">
                            <Clock size={24} />
                        </div>
                        <div>
                            <div className="stat-value">{Math.round(totalTime / 60)}h {totalTime % 60}m</div>
                            <div className="stat-label">Est. Duration</div>
                        </div>
                    </div>
                </div>

                {/* Map and Routes List */}
                <div className="grid-2">
                    <div className="card">
                        <div className="card-header">
                            <h2 className="card-title">Route Map</h2>
                        </div>
                        <RouteMap routes={routes} height={500} />
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <h2 className="card-title">Routes List</h2>
                        </div>

                        {routes.length === 0 ? (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                                <Truck size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
                                <p>No routes for this date</p>
                                <p style={{ fontSize: '14px', marginTop: '8px' }}>
                                    Run optimization to create routes
                                </p>
                            </div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                {routes.map((route, index) => (
                                    <div
                                        key={route.id}
                                        style={{
                                            padding: '16px',
                                            background: 'var(--bg-tertiary)',
                                            borderRadius: 'var(--radius-md)',
                                            border: '1px solid var(--border-primary)',
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                                            <div style={{
                                                width: '32px',
                                                height: '32px',
                                                borderRadius: '50%',
                                                background: ['#3b82f6', '#22c55e', '#f97316', '#a855f7', '#ec4899'][index % 5],
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                color: 'white',
                                                fontWeight: '600',
                                                fontSize: '14px',
                                            }}>
                                                {route.vehicle_code?.[1] || index + 1}
                                            </div>
                                            <div>
                                                <strong>{route.vehicle_code || route.vehicle_id}</strong>
                                                {route.driver_name && (
                                                    <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>
                                                        {route.driver_name}
                                                    </span>
                                                )}
                                            </div>
                                            <span className={`badge badge-${route.status === 'planned' ? 'processing' : 'geocoded'}`} style={{ marginLeft: 'auto' }}>
                                                {route.status}
                                            </span>
                                        </div>

                                        <div style={{ display: 'flex', gap: '24px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                                            <span><MapPin size={14} style={{ marginRight: '4px' }} />{route.total_stops} stops</span>
                                            <span><RouteIcon size={14} style={{ marginRight: '4px' }} />{route.total_distance_km.toFixed(1)} km</span>
                                            <span><Clock size={14} style={{ marginRight: '4px' }} />{route.total_time_minutes} min</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
