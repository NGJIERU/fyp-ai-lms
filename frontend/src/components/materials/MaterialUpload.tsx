"use client";

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline';

interface MaterialUploadProps {
    courseId: number;
    onUploadSuccess?: () => void;
    initialWeek?: number;
}

interface FileWithTitle {
    file: File;
    title: string;
    description: string;
}

const WEEKS = Array.from({ length: 14 }, (_, i) => i + 1);

export default function MaterialUpload({ courseId, onUploadSuccess, initialWeek = 1 }: MaterialUploadProps) {
    const [files, setFiles] = useState<FileWithTitle[]>([]);
    const [selectedWeek, setSelectedWeek] = useState<number>(initialWeek);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const newFiles = acceptedFiles.map(file => ({
            file,
            title: file.name.replace(/\.[^/.]+$/, ""),
            description: ''
        }));
        setFiles(prev => [...prev, ...newFiles]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
            'application/zip': ['.zip']
        },
        maxSize: 50 * 1024 * 1024
    });

    const updateFileTitle = (index: number, title: string) => {
        setFiles(prev => prev.map((f, i) => i === index ? { ...f, title } : f));
    };

    const updateFileDescription = (index: number, description: string) => {
        setFiles(prev => prev.map((f, i) => i === index ? { ...f, description } : f));
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleUpload = async () => {
        if (files.length === 0) return;

        setIsUploading(true);
        setError(null);
        setUploadProgress(0);

        try {
            const token = localStorage.getItem('token');
            const formData = new FormData();

            formData.append('week_number', selectedWeek.toString());

            if (files.length === 1) {
                // Single file upload
                formData.append('file', files[0].file);
                formData.append('title', files[0].title);
                if (files[0].description) {
                    formData.append('description', files[0].description);
                }

                const response = await fetch(`http://localhost:8000/api/v1/courses/${courseId}/materials/upload`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });

                if (response.status === 401) {
                    window.location.href = '/login';
                    throw new Error('Authentication expired');
                }

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Upload failed');
                }
            } else {
                // Batch upload
                files.forEach(({ file }) => formData.append('files', file));
                formData.append('titles', JSON.stringify(files.map(f => f.title)));
                formData.append('descriptions', JSON.stringify(files.map(f => f.description)));

                const response = await fetch(`http://localhost:8000/api/v1/courses/${courseId}/materials/upload-batch`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });

                if (response.status === 401) {
                    window.location.href = '/login';
                    throw new Error('Authentication expired');
                }

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Batch upload failed');
                }
            }

            setUploadProgress(100);
            setFiles([]);
            onUploadSuccess?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload failed');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
                <h3 className="text-base font-semibold leading-6 text-gray-900">Upload Course Materials</h3>
                <div className="mt-2 max-w-xl text-sm text-gray-500">
                    <p>Upload materials for students to access. Select the week and add files.</p>
                </div>

                {/* Week Selector */}
                <div className="mt-5">
                    <label htmlFor="week" className="block text-sm font-medium leading-6 text-gray-900">
                        Select Week
                    </label>
                    <select
                        id="week"
                        name="week"
                        value={selectedWeek}
                        onChange={(e) => setSelectedWeek(parseInt(e.target.value))}
                        className="mt-2 block w-full rounded-md border-0 py-1.5 pl-3 pr-10 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    >
                        {WEEKS.map(week => (
                            <option key={week} value={week}>
                                Week {week}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Dropzone */}
                <div className="mt-5">
                    <div
                        {...getRootProps()}
                        className={`mt-2 flex justify-center rounded-lg border border-dashed border-gray-900/25 px-6 py-10 ${isDragActive ? 'border-indigo-600 bg-indigo-50' : ''
                            }`}
                    >
                        <div className="text-center">
                            <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-300" aria-hidden="true" />
                            <div className="mt-4 flex text-sm leading-6 text-gray-600">
                                <input {...getInputProps()} />
                                <label className="relative cursor-pointer rounded-md bg-white font-semibold text-indigo-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-indigo-600 focus-within:ring-offset-2 hover:text-indigo-500">
                                    <span>Upload files</span>
                                </label>
                                <p className="pl-1">or drag and drop</p>
                            </div>
                            <p className="text-xs leading-5 text-gray-600">PDF, DOCX, PPTX, ZIP up to 50MB</p>
                        </div>
                    </div>
                </div>

                {/* File List */}
                {files.length > 0 && (
                    <div className="mt-6 space-y-4">
                        <h4 className="text-sm font-medium text-gray-900">Files to upload ({files.length})</h4>
                        {files.map((fileItem, index) => (
                            <div key={index} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-gray-900">{fileItem.file.name}</p>
                                        <p className="text-xs text-gray-500">
                                            {(fileItem.file.size / (1024 * 1024)).toFixed(2)} MB
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => removeFile(index)}
                                        type="button"
                                        className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                                    >
                                        <span className="sr-only">Remove</span>
                                        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                                        </svg>
                                    </button>
                                </div>
                                <div className="mt-2 space-y-2">
                                    <div>
                                        <label htmlFor={`title-${index}`} className="block text-xs font-medium text-gray-700">
                                            Title
                                        </label>
                                        <input
                                            type="text"
                                            id={`title-${index}`}
                                            value={fileItem.title}
                                            onChange={(e) => updateFileTitle(index, e.target.value)}
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor={`desc-${index}`} className="block text-xs font-medium text-gray-700">
                                            Description (optional)
                                        </label>
                                        <textarea
                                            id={`desc-${index}`}
                                            value={fileItem.description}
                                            onChange={(e) => updateFileDescription(index, e.target.value)}
                                            rows={2}
                                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Error */}
                {error && (
                    <div className="mt-4 rounded-md bg-red-50 p-4">
                        <div className="text-sm text-red-700">{error}</div>
                    </div>
                )}

                {/* Progress */}
                {isUploading && (
                    <div className="mt-4">
                        <div className="overflow-hidden rounded-full bg-gray-200">
                            <div
                                className="h-2 rounded-full bg-indigo-600 transition-all duration-300"
                                style={{ width: `${uploadProgress}%` }}
                            />
                        </div>
                        <p className="mt-1 text-sm text-gray-600">Uploading...</p>
                    </div>
                )}

                {/* Upload Button */}
                {files.length > 0 && (
                    <div className="mt-5">
                        <button
                            onClick={handleUpload}
                            disabled={isUploading}
                            type="button"
                            className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:bg-gray-400"
                        >
                            Upload {files.length} file{files.length > 1 ? 's' : ''} to Week {selectedWeek}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
