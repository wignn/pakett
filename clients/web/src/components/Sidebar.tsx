'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    Package,
    MapPin,
    Truck,
    Settings,
    BarChart3,
    AlertCircle,
    LogOut,
} from 'lucide-react';

interface SidebarProps {
    active?: string;
}

const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: '/' },
    { id: 'packages', label: 'Packages', icon: Package, href: '/packages' },
    { id: 'routes', label: 'Routes', icon: MapPin, href: '/routes' },
    { id: 'vehicles', label: 'Vehicles', icon: Truck, href: '/vehicles' },
    { id: 'verification', label: 'Verification', icon: AlertCircle, href: '/verification' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, href: '/analytics' },
];

export default function Sidebar({ active }: SidebarProps) {
    const pathname = usePathname();

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div style={{ padding: '0 20px', marginBottom: '32px' }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                }}>
                    <div style={{
                        width: '40px',
                        height: '40px',
                        background: 'var(--gradient-blue)',
                        borderRadius: 'var(--radius-md)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}>
                        <Package size={22} color="white" />
                    </div>
                    <div>
                        <h1 style={{ fontSize: '18px', fontWeight: '700' }}>Paket</h1>
                        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Routing System</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav>
                <div style={{ padding: '0 12px' }}>
                    <p style={{
                        fontSize: '11px',
                        fontWeight: '600',
                        color: 'var(--text-muted)',
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        padding: '0 8px',
                        marginBottom: '8px'
                    }}>
                        Menu
                    </p>

                    {menuItems.map((item) => {
                        const isActive = active === item.id || pathname === item.href;
                        const Icon = item.icon;

                        return (
                            <Link
                                key={item.id}
                                href={item.href}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '12px',
                                    padding: '12px 16px',
                                    borderRadius: 'var(--radius-md)',
                                    marginBottom: '4px',
                                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                                    background: isActive ? 'var(--bg-tertiary)' : 'transparent',
                                    transition: 'var(--transition-fast)',
                                    position: 'relative',
                                }}
                            >
                                {isActive && (
                                    <div style={{
                                        position: 'absolute',
                                        left: 0,
                                        top: '50%',
                                        transform: 'translateY(-50%)',
                                        width: '3px',
                                        height: '24px',
                                        background: 'var(--gradient-blue)',
                                        borderRadius: '0 4px 4px 0',
                                    }} />
                                )}
                                <Icon size={20} />
                                <span style={{ fontSize: '14px', fontWeight: isActive ? '500' : '400' }}>
                                    {item.label}
                                </span>
                            </Link>
                        );
                    })}
                </div>
            </nav>

            {/* Bottom section */}
            <div style={{
                position: 'absolute',
                bottom: '20px',
                left: '0',
                right: '0',
                padding: '0 12px',
            }}>
                <Link
                    href="/settings"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '12px 16px',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--text-secondary)',
                        transition: 'var(--transition-fast)',
                    }}
                >
                    <Settings size={20} />
                    <span style={{ fontSize: '14px' }}>Settings</span>
                </Link>
            </div>
        </aside>
    );
}
