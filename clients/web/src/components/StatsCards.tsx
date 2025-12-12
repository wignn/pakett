'use client';

import { Package, MapPin, Truck, AlertTriangle, TrendingUp } from 'lucide-react';
import { Stats } from '@/lib/types';

interface StatsCardsProps {
    stats: Stats | null;
    loading?: boolean;
}

export default function StatsCards({ stats, loading }: StatsCardsProps) {
    const cards = [
        {
            label: 'Total Packages',
            value: stats?.total_packages ?? 0,
            icon: Package,
            color: 'blue',
            change: '+12%',
            positive: true,
        },
        {
            label: 'Geocoded',
            value: stats?.geocoded_packages ?? 0,
            icon: MapPin,
            color: 'green',
            change: `${((stats?.avg_confidence ?? 0) * 100).toFixed(0)}% avg conf`,
            positive: true,
        },
        {
            label: 'Routes Today',
            value: stats?.total_routes_today ?? 0,
            icon: Truck,
            color: 'purple',
            change: `${stats?.active_vehicles ?? 0} vehicles`,
            positive: true,
        },
        {
            label: 'Need Verification',
            value: stats?.verification_needed ?? 0,
            icon: AlertTriangle,
            color: 'orange',
            change: stats?.verification_needed && stats.verification_needed > 5 ? 'Action needed' : 'All good',
            positive: (stats?.verification_needed ?? 0) <= 5,
        },
    ];

    return (
        <div className="stats-grid">
            {cards.map((card, index) => {
                const Icon = card.icon;

                return (
                    <div
                        key={card.label}
                        className={`stat-card fade-in ${loading ? 'loading' : ''}`}
                        style={{ animationDelay: `${index * 50}ms` }}
                    >
                        <div className={`stat-icon ${card.color}`}>
                            <Icon size={24} />
                        </div>
                        <div>
                            <div className="stat-value">
                                {loading ? '—' : card.value.toLocaleString()}
                            </div>
                            <div className="stat-label">{card.label}</div>
                            <div className={`stat-change ${card.positive ? 'positive' : 'negative'}`}>
                                {loading ? '' : card.change}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
