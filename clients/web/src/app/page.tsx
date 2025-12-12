'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import StatsCards from '@/components/StatsCards';
import PackagesTable from '@/components/PackagesTable';
import RouteMap from '@/components/RouteMap';
import { Package, Stats, Route } from '@/lib/types';
import { fetchPackages, fetchStats, fetchRoutes } from '@/lib/api';

export default function DashboardPage() {
    const [packages, setPackages] = useState<Package[]>([]);
    const [stats, setStats] = useState<Stats | null>(null);
    const [routes, setRoutes] = useState<Route[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        try {
            setLoading(true);
            const [pkgData, statsData, routesData] = await Promise.all([
                fetchPackages(),
                fetchStats(),
                fetchRoutes(),
            ]);
            setPackages(pkgData);
            setStats(statsData);
            setRoutes(routesData);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="layout">
            <Sidebar active="dashboard" />

            <main className="main-content">
                <div className="page-header">
                    <h1 className="page-title">Dashboard</h1>
                    <p className="page-description">
                        Real-time overview of package processing and route optimization
                    </p>
                </div>

                {/* Stats Cards */}
                <StatsCards stats={stats} loading={loading} />

                {/* Main Grid */}
                <div className="grid-2" style={{ marginTop: '24px' }}>
                    {/* Route Map */}
                    <div className="card">
                        <div className="card-header">
                            <div>
                                <h2 className="card-title">Route Overview</h2>
                                <p className="card-subtitle">Today's delivery routes</p>
                            </div>
                            <button className="btn btn-secondary btn-sm">
                                Optimize Routes
                            </button>
                        </div>
                        <RouteMap routes={routes} />
                    </div>

                    {/* Recent Packages */}
                    <div className="card">
                        <div className="card-header">
                            <div>
                                <h2 className="card-title">Recent Packages</h2>
                                <p className="card-subtitle">Latest ingested packages</p>
                            </div>
                            <button className="btn btn-secondary btn-sm" onClick={loadData}>
                                Refresh
                            </button>
                        </div>
                        <PackagesTable packages={packages.slice(0, 8)} compact />
                    </div>
                </div>
            </main>
        </div>
    );
}
