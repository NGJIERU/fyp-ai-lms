"use client";

import { EllipsisVerticalIcon, ArrowDownTrayIcon, EyeIcon, TrashIcon } from '@heroicons/react/20/solid';
import { DocumentIcon, DocumentTextIcon, PresentationChartBarIcon, ArchiveBoxIcon } from '@heroicons/react/24/outline';

interface Material {
    id: number;
    title: string;
    description: string | null;
    file_name: string;
    file_size: number;
    content_type: string;
    uploaded_at: string;
    uploader_name: string | null;
    download_count: number;
    view_count: number;
    material_type?: string;
    source?: string;
}

interface MaterialCardProps {
    material: Material;
    onDownload: () => void;
    onDelete: () => void;
    onPreview: () => void;
}

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ');
}

export default function MaterialCard({ material, onDownload, onDelete, onPreview }: MaterialCardProps) {
    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    };

    const getFileIcon = () => {
        const type = material.content_type;
        if (type?.includes('pdf')) {
            return { Icon: DocumentTextIcon, color: 'bg-red-600' };
        } else if (type?.includes('word') || type?.includes('document')) {
            return { Icon: DocumentIcon, color: 'bg-blue-600' };
        } else if (type?.includes('presentation')) {
            return { Icon: PresentationChartBarIcon, color: 'bg-orange-600' };
        } else {
            return { Icon: ArchiveBoxIcon, color: 'bg-gray-600' };
        }
    };

    const { Icon, color } = getFileIcon();
    const isUploaded = material.material_type === 'uploaded' || material.source === 'Manual Upload';

    return (
        <li className="col-span-1 flex rounded-md shadow-sm">
            <div
                className={classNames(
                    color,
                    'flex w-16 shrink-0 items-center justify-center rounded-l-md text-sm font-medium text-white'
                )}
            >
                <Icon className="h-8 w-8" aria-hidden="true" />
            </div>
            <div className="flex flex-1 flex-col justify-between truncate rounded-r-md border-b border-r border-t border-gray-200 bg-white">
                <div className="flex-1 truncate px-4 py-3">
                    <div className="flex items-center justify-between">
                        <h3 className="truncate text-sm font-medium text-gray-900">
                            {material.title}
                        </h3>
                        <span className={classNames(
                            isUploaded ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800',
                            'inline-flex shrink-0 rounded-full px-2 py-0.5 text-xs font-medium'
                        )}>
                            {isUploaded ? 'Manual' : 'AI'}
                        </span>
                    </div>
                    <p className="mt-1 text-xs text-gray-500 truncate">{material.file_name}</p>
                    {material.description && (
                        <p className="mt-1 text-xs text-gray-600 line-clamp-2">{material.description}</p>
                    )}
                    <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                        <span>{formatFileSize(material.file_size)}</span>
                        <span>•</span>
                        <span>{formatDate(material.uploaded_at)}</span>
                    </div>
                    {material.uploader_name && (
                        <p className="mt-1 text-xs text-gray-500">By {material.uploader_name}</p>
                    )}
                    <div className="mt-2 flex items-center space-x-3 text-xs text-gray-500">
                        <span className="flex items-center">
                            <EyeIcon className="h-3.5 w-3.5 mr-1" />
                            {material.view_count || 0}
                        </span>
                        <span className="flex items-center">
                            <ArrowDownTrayIcon className="h-3.5 w-3.5 mr-1" />
                            {material.download_count || 0}
                        </span>
                    </div>
                </div>
                <div className="border-t border-gray-200 bg-gray-50 px-4 py-2">
                    <div className="flex justify-between items-center">
                        <div className="flex space-x-2">
                            {material.content_type === 'application/pdf' && (
                                <button
                                    onClick={onPreview}
                                    className="text-xs text-indigo-600 hover:text-indigo-900 font-medium"
                                >
                                    Preview
                                </button>
                            )}
                            <button
                                onClick={onDownload}
                                className="text-xs text-indigo-600 hover:text-indigo-900 font-medium"
                            >
                                Download
                            </button>
                        </div>
                        <button
                            onClick={onDelete}
                            className="inline-flex items-center text-red-600 hover:text-red-900"
                        >
                            <TrashIcon className="h-4 w-4" />
                        </button>
                    </div>
                </div>
            </div>
        </li>
    );
}
