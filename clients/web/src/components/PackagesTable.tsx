'use client';

import { useState } from 'react';
import { Package } from '@/lib/types';
import { Eye, MapPin, Check, AlertTriangle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface PackagesTableProps {
    packages: Package[];
    compact?: boolean;
    onSelect?: (pkg: Package) => void;
}

const statusConfig: Record<string, { label: string; className: string }> = {
    pending: { label: 'Pending', className: 'badge-pending' },
    processing: { label: 'Processing', className: 'badge-processing' },
    parsed: { label: 'Parsed', className: 'badge-processing' },
    geocoded: { label: 'Geocoded', className: 'badge-geocoded' },
    routed: { label: 'Routed', className: 'badge-routed' },
    delivered: { label: 'Delivered', className: 'badge-geocoded' },
    verification_needed: { label: 'Verify', className: 'badge-verification' },
    failed: { label: 'Failed', className: 'badge-failed' },
};

export default function PackagesTable({ packages, compact, onSelect }: PackagesTableProps) {
    if (packages.length === 0) {
        return (
            <div style={{
                padding: '40px',
                textAlign: 'center',
                color: 'var(--text-muted)'
            }}>
                <Package size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
                <p>No packages found</p>
            </div>
        );
    }

    return (
        <div className="table-container">
            <table className="table">
                <thead>
                    <tr>
                        <th>Package ID</th>
                        {!compact && <th>Device</th>}
                        <th>Address (OCR)</th>
                        <th>Confidence</th>
                        <th>Status</th>
                        <th>Time</th>
                        {!compact && <th>Actions</th>}
                    </tr>
                </thead>
                <tbody>
                    {packages.map((pkg) => {
                        const status = statusConfig[pkg.status] || statusConfig.pending;
                        const confidence = (pkg.ocr_confidence * 100).toFixed(0);
                        const isLowConfidence = pkg.ocr_confidence < 0.7;

                        return (
                            <tr key={pkg.id} onClick={() => onSelect?.(pkg)} style={{ cursor: onSelect ? 'pointer' : 'default' }}>
                                <td>
                                    <span style={{ fontFamily: 'monospace', fontSize: '13px' }}>
                                        {pkg.package_id}
                                    </span>
                                </td>
                                {!compact && (
                                    <td style={{ color: 'var(--text-secondary)' }}>
                                        {pkg.device_id}
                                    </td>
                                )}
                                <td>
                                    <div style={{
                                        maxWidth: compact ? '200px' : '300px',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: 'nowrap',
                                        fontSize: '13px'
                                    }}>
                                        {pkg.ocr_text}
                                    </div>
                                </td>
                                <td>
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                        color: isLowConfidence ? 'var(--accent-orange)' : 'var(--accent-green)'
                                    }}>
                                        {isLowConfidence ? <AlertTriangle size={14} /> : <Check size={14} />}
                                        <span>{confidence}%</span>
                                    </div>
                                </td>
                                <td>
                                    <span className={`badge ${status.className}`}>
                                        {status.label}
                                    </span>
                                </td>
                                <td style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                                    {formatDistanceToNow(new Date(pkg.created_at), { addSuffix: true })}
                                </td>
                                {!compact && (
                                    <td>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <button className="btn btn-icon btn-secondary" title="View Details">
                                                <Eye size={16} />
                                            </button>
                                            <button className="btn btn-icon btn-secondary" title="View on Map">
                                                <MapPin size={16} />
                                            </button>
                                        </div>
                                    </td>
                                )}
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
