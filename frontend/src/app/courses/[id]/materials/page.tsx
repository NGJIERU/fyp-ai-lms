"use client";

import { useParams } from 'next/navigation';
import MaterialManagement from '@/components/materials/MaterialManagement';
import { useState, useEffect } from 'react';

export default function CourseMaterialsPage() {
    const params = useParams();
    const courseId = parseInt(params.id as string);
    const [userRole, setUserRole] = useState<'lecturer' | 'student'>('lecturer');

    // For demo purposes, toggle between roles
    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-7xl mx-auto px-4">
                {/* Header */}
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-900">Course Materials</h1>
                    <p className="text-gray-600 mt-2">Upload and manage course materials</p>
                </div>

                {/* Role Toggle (for demo) */}
                <div className="mb-6 bg-white p-4 rounded-lg shadow">
                    <label className="text-sm font-medium text-gray-700 mr-4">
                        View as:
                    </label>
                    <select
                        value={userRole}
                        onChange={(e) => setUserRole(e.target.value as 'lecturer' | 'student')}
                        className="px-3 py-2 border border-gray-300 rounded-md"
                    >
                        <option value="lecturer">Lecturer</option>
                        <option value="student">Student</option>
                    </select>
                    <span className="ml-3 text-sm text-gray-500">
                        {userRole === 'lecturer' ? '(Can upload & manage)' : '(Can view & download only)'}
                    </span>
                </div>

                {/* Materials Component */}
                <MaterialManagement
                    courseId={courseId}
                    userRole={userRole}
                />
            </div>
        </div>
    );
}
