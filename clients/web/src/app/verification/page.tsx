'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { Package, ParsedAddress } from '@/lib/types';
import { fetchPackages, parseAddress, geocodeAddress } from '@/lib/api';
import { Check, X, MapPin, AlertTriangle, Eye, ChevronRight } from 'lucide-react';

export default function VerificationPage() {
    const [packages, setPackages] = useState<Package[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedPkg, setSelectedPkg] = useState<Package | null>(null);
    const [parsedAddress, setParsedAddress] = useState<ParsedAddress | null>(null);
    const [verifying, setVerifying] = useState(false);

    useEffect(() => {
        loadPackages();
    }, []);

    async function loadPackages() {
        try {
            setLoading(true);
            const data = await fetchPackages(100);
            // Filter only packages needing verification
            const needsVerification = data.filter(
                p => p.status === 'verification_needed' || p.ocr_confidence < 0.7
            );
            setPackages(needsVerification);
        } catch (error) {
            console.error('Failed to load packages:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleSelectPackage(pkg: Package) {
        setSelectedPkg(pkg);
        setVerifying(true);

        try {
            const parsed = await parseAddress(pkg.ocr_text);
            setParsedAddress(parsed);
        } catch (error) {
            console.error('Failed to parse address:', error);
            setParsedAddress(null);
        } finally {
            setVerifying(false);
        }
    }

    async function handleApprove() {
        if (!selectedPkg || !parsedAddress) return;

        try {
            // In real implementation, this would update the package status
            setPackages(prev => prev.filter(p => p.id !== selectedPkg.id));
            setSelectedPkg(null);
            setParsedAddress(null);
        } catch (error) {
            console.error('Failed to approve:', error);
        }
    }

    async function handleReject() {
        if (!selectedPkg) return;

        // In real implementation, this would mark as failed
        setPackages(prev => prev.filter(p => p.id !== selectedPkg.id));
        setSelectedPkg(null);
        setParsedAddress(null);
    }

    return (
        <div className="layout">
            <Sidebar active="verification" />

            <main className="main-content">
                <div className="page-header">
                    <h1 className="page-title">Address Verification</h1>
                    <p className="page-description">
                        Review and correct low-confidence addresses
                    </p>
                </div>

                <div className="grid-2">
                    {/* Queue */}
                    <div className="card">
                        <div className="card-header">
                            <div>
                                <h2 className="card-title">Verification Queue</h2>
                                <p className="card-subtitle">{packages.length} items pending</p>
                            </div>
                        </div>

                        {loading ? (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                                Loading...
                            </div>
                        ) : packages.length === 0 ? (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                                <Check size={48} style={{ marginBottom: '16px', color: 'var(--accent-green)' }} />
                                <p>All addresses verified!</p>
                            </div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {packages.map(pkg => (
                                    <button
                                        key={pkg.id}
                                        onClick={() => handleSelectPackage(pkg)}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '12px',
                                            padding: '14px 16px',
                                            background: selectedPkg?.id === pkg.id ? 'var(--bg-hover)' : 'var(--bg-tertiary)',
                                            border: selectedPkg?.id === pkg.id ? '1px solid var(--accent-blue)' : '1px solid var(--border-primary)',
                                            borderRadius: 'var(--radius-md)',
                                            cursor: 'pointer',
                                            textAlign: 'left',
                                            width: '100%',
                                            transition: 'var(--transition-fast)',
                                        }}
                                    >
                                        <AlertTriangle
                                            size={20}
                                            color={pkg.ocr_confidence < 0.5 ? 'var(--accent-red)' : 'var(--accent-orange)'}
                                        />
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontWeight: '500', marginBottom: '4px' }}>
                                                {pkg.package_id}
                                            </div>
                                            <div style={{
                                                fontSize: '13px',
                                                color: 'var(--text-secondary)',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                whiteSpace: 'nowrap',
                                                maxWidth: '300px'
                                            }}>
                                                {pkg.ocr_text}
                                            </div>
                                        </div>
                                        <div style={{
                                            fontSize: '13px',
                                            color: pkg.ocr_confidence < 0.5 ? 'var(--accent-red)' : 'var(--accent-orange)'
                                        }}>
                                            {(pkg.ocr_confidence * 100).toFixed(0)}%
                                        </div>
                                        <ChevronRight size={18} color="var(--text-muted)" />
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Verification Panel */}
                    <div className="card">
                        <div className="card-header">
                            <h2 className="card-title">Verification Panel</h2>
                        </div>

                        {!selectedPkg ? (
                            <div style={{ padding: '60px 40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                                <Eye size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
                                <p>Select a package to verify</p>
                            </div>
                        ) : verifying ? (
                            <div style={{ padding: '60px 40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                                <div className="loading">Parsing address...</div>
                            </div>
                        ) : (
                            <div>
                                {/* OCR Text */}
                                <div style={{ marginBottom: '24px' }}>
                                    <label className="input-label">Original OCR Text</label>
                                    <div style={{
                                        padding: '12px 16px',
                                        background: 'var(--bg-tertiary)',
                                        borderRadius: 'var(--radius-md)',
                                        border: '1px solid var(--border-primary)',
                                        fontSize: '14px',
                                    }}>
                                        {selectedPkg.ocr_text}
                                    </div>
                                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                        Confidence: {(selectedPkg.ocr_confidence * 100).toFixed(0)}%
                                    </p>
                                </div>

                                {/* Parsed Address */}
                                {parsedAddress && (
                                    <div style={{ marginBottom: '24px' }}>
                                        <label className="input-label">Parsed Address</label>
                                        <div style={{
                                            padding: '16px',
                                            background: 'var(--bg-tertiary)',
                                            borderRadius: 'var(--radius-md)',
                                            border: '1px solid var(--border-primary)',
                                        }}>
                                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                                                {parsedAddress.street && (
                                                    <div>
                                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Street</span>
                                                        <p>{parsedAddress.street} {parsedAddress.house_number}</p>
                                                    </div>
                                                )}
                                                {(parsedAddress.rt || parsedAddress.rw) && (
                                                    <div>
                                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>RT/RW</span>
                                                        <p>RT {parsedAddress.rt || '-'} / RW {parsedAddress.rw || '-'}</p>
                                                    </div>
                                                )}
                                                {parsedAddress.subdistrict && (
                                                    <div>
                                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Subdistrict</span>
                                                        <p>{parsedAddress.subdistrict}</p>
                                                    </div>
                                                )}
                                                {parsedAddress.city && (
                                                    <div>
                                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>City</span>
                                                        <p>{parsedAddress.city}</p>
                                                    </div>
                                                )}
                                                {parsedAddress.postal_code && (
                                                    <div>
                                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Postal Code</span>
                                                        <p>{parsedAddress.postal_code}</p>
                                                    </div>
                                                )}
                                            </div>

                                            {parsedAddress.corrections_applied?.length > 0 && (
                                                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-primary)' }}>
                                                    <span style={{ fontSize: '12px', color: 'var(--accent-blue)' }}>
                                                        Corrections applied: {parsedAddress.corrections_applied.join(', ')}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                            Parse confidence: {(parsedAddress.confidence * 100).toFixed(0)}%
                                        </p>
                                    </div>
                                )}

                                {/* Actions */}
                                <div style={{ display: 'flex', gap: '12px' }}>
                                    <button className="btn btn-danger" onClick={handleReject} style={{ flex: 1 }}>
                                        <X size={18} />
                                        Reject
                                    </button>
                                    <button className="btn btn-success" onClick={handleApprove} style={{ flex: 1 }}>
                                        <Check size={18} />
                                        Approve
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
