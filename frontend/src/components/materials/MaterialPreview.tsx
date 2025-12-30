"use client";

import { useEffect, useState } from 'react';

interface Material {
    id: number;
    title: string;
    file_name: string;
    content_type: string;
}

interface MaterialPreviewProps {
    material: Material;
    courseId: number;
    onClose: () => void;
}

export default function MaterialPreview({ material, courseId, onClose }: MaterialPreviewProps) {
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPdf = async () => {
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
                    throw new Error('Failed to load PDF');
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                setPdfUrl(url);
            } catch (err) {
                alert('Failed to load preview');
                onClose();
            } finally {
                setLoading(false);
            }
        };

        if (material.content_type === 'application/pdf') {
            fetchPdf();
        }

        return () => {
            if (pdfUrl) {
                window.URL.revokeObjectURL(pdfUrl);
            }
        };
    }, [material, courseId]);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg w-full max-w-6xl h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b">
                    <div>
                        <h3 className="text-lg font-semibold">{material.title}</h3>
                        <p className="text-sm text-gray-500">{material.file_name}</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-500 hover:text-gray-700"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden">
                    {loading ? (
                        <div className="flex justify-center items-center h-full">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                        </div>
                    ) : pdfUrl ? (
                        <iframe
                            src={pdfUrl}
                            className="w-full h-full"
                            title="PDF Preview"
                        />
                    ) : (
                        <div className="flex justify-center items-center h-full text-gray-500">
                            Preview not available for this file type
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
