'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import PackagesTable from '@/components/PackagesTable';
import { Package } from '@/lib/types';
import { fetchPackages, ingestPackage } from '@/lib/api';
import { Plus, Search, Filter, RefreshCw } from 'lucide-react';

export default function PackagesPage() {
    const [packages, setPackages] = useState<Package[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [showIngestModal, setShowIngestModal] = useState(false);

    useEffect(() => {
        loadPackages();
    }, []);

    async function loadPackages() {
        try {
            setLoading(true);
            const data = await fetchPackages(100);
            setPackages(data);
        } catch (error) {
            console.error('Failed to load packages:', error);
        } finally {
            setLoading(false);
        }
    }

    // Filter packages
    const filteredPackages = packages.filter(pkg => {
        const matchesSearch =
            pkg.package_id.toLowerCase().includes(search.toLowerCase()) ||
            pkg.ocr_text.toLowerCase().includes(search.toLowerCase());
        const matchesStatus = statusFilter === 'all' || pkg.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    return (
        <div className="layout">
            <Sidebar active="packages" />

            <main className="main-content">
                <div className="page-header">
                    <h1 className="page-title">Packages</h1>
                    <p className="page-description">
                        Manage all ingested packages and their processing status
                    </p>
                </div>

                {/* Actions Bar */}
                <div className="card" style={{ marginBottom: '24px' }}>
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                        {/* Search */}
                        <div style={{ flex: 1, minWidth: '250px' }}>
                            <div style={{ position: 'relative' }}>
                                <Search
                                    size={18}
                                    style={{
                                        position: 'absolute',
                                        left: '12px',
                                        top: '50%',
                                        transform: 'translateY(-50%)',
                                        color: 'var(--text-muted)'
                                    }}
                                />
                                <input
                                    type="text"
                                    className="input"
                                    placeholder="Search packages..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    style={{ paddingLeft: '40px' }}
                                />
                            </div>
                        </div>

                        {/* Status Filter */}
                        <select
                            className="input"
                            style={{ width: 'auto', minWidth: '150px' }}
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                        >
                            <option value="all">All Status</option>
                            <option value="pending">Pending</option>
                            <option value="geocoded">Geocoded</option>
                            <option value="routed">Routed</option>
                            <option value="verification_needed">Need Verification</option>
                            <option value="failed">Failed</option>
                        </select>

                        {/* Actions */}
                        <button className="btn btn-secondary" onClick={loadPackages} disabled={loading}>
                            <RefreshCw size={16} className={loading ? 'loading' : ''} />
                            Refresh
                        </button>
                        <button className="btn btn-primary" onClick={() => setShowIngestModal(true)}>
                            <Plus size={16} />
                            Ingest Package
                        </button>
                    </div>
                </div>

                {/* Packages Table */}
                <div className="card">
                    <div className="card-header">
                        <div>
                            <h2 className="card-title">All Packages</h2>
                            <p className="card-subtitle">
                                Showing {filteredPackages.length} of {packages.length} packages
                            </p>
                        </div>
                    </div>

                    <PackagesTable packages={filteredPackages} />
                </div>

                {/* Ingest Modal */}
                {showIngestModal && (
                    <IngestModal
                        onClose={() => setShowIngestModal(false)}
                        onSuccess={() => {
                            setShowIngestModal(false);
                            loadPackages();
                        }}
                    />
                )}
            </main>
        </div>
    );
}

interface IngestModalProps {
    onClose: () => void;
    onSuccess: () => void;
}

function IngestModal({ onClose, onSuccess }: IngestModalProps) {
    const [formData, setFormData] = useState({
        device_id: 'web-console',
        package_id: `PKT${Date.now()}`,
        ocr_text: '',
        ocr_confidence: 0.9,
        priority: 'standard',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();

        if (!formData.ocr_text.trim()) {
            setError('Address text is required');
            return;
        }

        try {
            setLoading(true);
            setError('');
            await ingestPackage(formData);
            onSuccess();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to ingest package');
        } finally {
            setLoading(false);
        }
    }

    return (
        <div style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
        }}>
            <div className="card" style={{ width: '500px', maxWidth: '90vw' }}>
                <div className="card-header">
                    <h2 className="card-title">Ingest New Package</h2>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label className="input-label">Package ID</label>
                        <input
                            type="text"
                            className="input"
                            value={formData.package_id}
                            onChange={(e) => setFormData({ ...formData, package_id: e.target.value })}
                        />
                    </div>

                    <div className="input-group">
                        <label className="input-label">Address Text (OCR)</label>
                        <textarea
                            className="input"
                            rows={3}
                            placeholder="e.g., Jalan Merdeka 45 RT 02/RW 03, Kebayoran Lama, Jakarta Selatan 12220"
                            value={formData.ocr_text}
                            onChange={(e) => setFormData({ ...formData, ocr_text: e.target.value })}
                        />
                    </div>

                    <div className="input-group">
                        <label className="input-label">Priority</label>
                        <select
                            className="input"
                            value={formData.priority}
                            onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                        >
                            <option value="standard">Standard</option>
                            <option value="high">High</option>
                            <option value="urgent">Urgent</option>
                        </select>
                    </div>

                    {error && (
                        <p style={{ color: 'var(--accent-red)', marginBottom: '16px' }}>{error}</p>
                    )}

                    <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? 'Processing...' : 'Ingest Package'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
