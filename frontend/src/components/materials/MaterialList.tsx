"use client";

import { useState, useEffect } from 'react';
import MaterialCard from './MaterialCard';
import MaterialPreview from './MaterialPreview';
import { MagnifyingGlassIcon } from '@heroicons/react/20/solid';

interface Material {
    id: number;
    title: string;
    description: string | null;
    file_name: string;
    file_size: number;
    content_type: string;
    uploaded_at: string;
    updated_at: string;
    uploader_name: string | null;
    download_count: number;
    view_count: number;
    last_downloaded_at: string | null;
    material_type?: string;
    source?: string;
}

interface MaterialListProps {
    courseId: number;
    refreshTrigger?: number;
    weekNumber?: number;
}

export default function MaterialList({ courseId, refreshTrigger, weekNumber }: MaterialListProps) {
    const [materials, setMaterials] = useState<Material[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [previewMaterial, setPreviewMaterial] = useState<Material | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchMaterials();
    }, [courseId, refreshTrigger, weekNumber]);

    const fetchMaterials = async () => {
        try {
            setLoading(true);
            setError(null);
            const token = localStorage.getItem('token');

            let url = `${process.env.NEXT_PUBLIC_API_BASE_URL || ""}/courses/${courseId}/materials`;
            if (weekNumber) {
                url += `?week_number=${weekNumber}`;
            }

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                window.location.href = '/login';
                throw new Error('Authentication expired. Please logging in again.');
            }

            if (!response.ok) {
                throw new Error('Failed to fetch materials');
            }

            const data = await response.json();
            setMaterials(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load materials');
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async (material: Material) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_BASE_URL || ""}/courses/${courseId}/materials/${material.id}/download`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Download failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = material.file_name;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            // Refresh to update download count
            fetchMaterials();
        } catch (err) {
            alert('Failed to download file');
        }
    };

    const handleDelete = async (materialId: number) => {
        if (!confirm('Are you sure you want to delete this material?')) return;

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_BASE_URL || ""}/courses/${courseId}/materials/${materialId}`,
                {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Delete failed');
            }

            fetchMaterials();
        } catch (err) {
            alert('Failed to delete material');
        }
    };

    const filteredMaterials = materials.filter(material =>
        material.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        material.file_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-700">{error}</div>
            </div>
        );
    }

    return (
        <div>
            <div className="sm:flex sm:items-center sm:justify-between mb-6">
                <div>
                    <h2 className="text-lg font-medium text-gray-900">Course Materials</h2>
                    <p className="mt-1 text-sm text-gray-500">
                        {materials.length} material{materials.length !== 1 ? 's' : ''} available
                    </p>
                </div>
            </div>

            {/* Search */}
            <div className="mb-6">
                <label htmlFor="search" className="sr-only">
                    Search materials
                </label>
                <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                        <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                    </div>
                    <input
                        type="text"
                        name="search"
                        id="search"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="block w-full rounded-md border-0 py-1.5 pl-10 pr-3 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                        placeholder="Search materials..."
                    />
                </div>
            </div>

            {/* Materials Grid */}
            {filteredMaterials.length === 0 ? (
                <div className="text-center py-12">
                    <svg
                        className="mx-auto h-12 w-12 text-gray-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
                        />
                    </svg>
                    <h3 className="mt-2 text-sm font-semibold text-gray-900">No materials</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        {searchQuery ? 'No materials match your search' : 'Get started by uploading a material'}
                    </p>
                </div>
            ) : (
                <ul role="list" className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                    {filteredMaterials.map(material => (
                        <MaterialCard
                            key={material.id}
                            material={material}
                            onDownload={() => handleDownload(material)}
                            onDelete={() => handleDelete(material.id)}
                            onPreview={() => setPreviewMaterial(material)}
                        />
                    ))}
                </ul>
            )}

            {/* Preview Modal */}
            {previewMaterial && (
                <MaterialPreview
                    material={previewMaterial}
                    courseId={courseId}
                    onClose={() => setPreviewMaterial(null)}
                />
            )}
        </div>
    );
}
