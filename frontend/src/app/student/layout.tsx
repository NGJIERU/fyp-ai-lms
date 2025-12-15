"use client";

import StudentSidebar from "@/components/layout/StudentSidebar";
import { useStudyTracker } from "@/hooks/useStudyTracker";

export default function StudentLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    useStudyTracker();

    return (
        <div className="min-h-screen bg-gray-50 md:flex">
            <StudentSidebar />
            <main className="flex-1">
                {children}
            </main>
        </div>
    );
}
