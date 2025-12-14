import StudentSidebar from "@/components/layout/StudentSidebar";

export default function StudentLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-gray-50 md:flex">
            <StudentSidebar />
            <main className="flex-1">
                {children}
            </main>
        </div>
    );
}
