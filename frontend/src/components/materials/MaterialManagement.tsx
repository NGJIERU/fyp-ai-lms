"use client";

import { useState } from 'react';
import WeekSidebar from './WeekSidebar';
import MaterialList from './MaterialList';
import UploadModal from './UploadModal';
import { PlusIcon } from '@heroicons/react/20/solid';

interface MaterialManagementProps {
    courseId: number;
    userRole: 'lecturer' | 'student';
}

export default function MaterialManagement({ courseId, userRole }: MaterialManagementProps) {
    const [selectedWeek, setSelectedWeek] = useState<number>(1);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    const handleUploadSuccess = () => {
        setRefreshTrigger(prev => prev + 1);
    };

    return (
        <div className="flex h-[calc(100vh-100px)] overflow-hidden bg-white rounded-lg shadow">
            {/* Sidebar */}
            <div className="w-64 border-r border-gray-200 bg-gray-50 pt-5 pb-4 overflow-y-auto">
                <WeekSidebar
                    selectedWeek={selectedWeek}
                    onSelectWeek={setSelectedWeek}
                // weekCounts={...} // TODO: Add counts later
                />
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Header */}
                <div className="border-b border-gray-200 px-6 py-4 bg-white flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-semibold text-gray-900">
                            Week {selectedWeek} Materials
                        </h2>
                        <p className="mt-1 text-sm text-gray-500">
                            Browse and access course materials for Week {selectedWeek}.
                        </p>
                    </div>

                    {userRole === 'lecturer' && (
                        <button
                            onClick={() => setIsUploadModalOpen(true)}
                            className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                        >
                            <PlusIcon className="-ml-0.5 mr-1.5 h-5 w-5" aria-hidden="true" />
                            Upload Material
                        </button>
                    )}
                </div>

                {/* Material List */}
                <div className="flex-1 overflow-y-auto px-6 py-6">
                    <MaterialList
                        courseId={courseId}
                        weekNumber={selectedWeek}
                        refreshTrigger={refreshTrigger}
                    />
                </div>
            </div>

            {/* Upload Modal */}
            {userRole === 'lecturer' && (
                <UploadModal
                    isOpen={isUploadModalOpen}
                    onClose={() => setIsUploadModalOpen(false)}
                    courseId={courseId}
                    selectedWeek={selectedWeek}
                    onUploadSuccess={handleUploadSuccess}
                />
            )}
        </div>
    );
}
