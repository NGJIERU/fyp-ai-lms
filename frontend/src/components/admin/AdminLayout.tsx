import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode } from "react";

interface AdminLayoutProps {
    children: ReactNode;
    headerTitle?: string;
    headerSubtitle?: string;
}

export function AdminLayout({ children, headerTitle, headerSubtitle }: AdminLayoutProps) {
    const pathname = usePathname();
    const router = useRouter();

    const navItems = [
        { label: "Users", href: "/admin/users" },
        { label: "Courses", href: "/admin/courses" },
        { label: "Activity Logs", href: "/admin/activity" },
        { label: "System Health", href: "/admin/health" },
    ];

    function handleLogout() {
        localStorage.removeItem("access_token");
        router.push("/login");
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Top Navigation Bar */}
            <nav className="bg-white border-b border-gray-200">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 justify-between">
                        <div className="flex">
                            <div className="flex flex-shrink-0 items-center">
                                <span className="text-xl font-bold text-indigo-600">LMS Admin</span>
                            </div>
                            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                                {navItems.map((item) => (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        className={`inline-flex items-center border-b-2 px-1 pt-1 text-sm font-medium ${pathname === item.href || pathname?.startsWith(item.href)
                                                ? "border-indigo-500 text-gray-900"
                                                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                                            }`}
                                    >
                                        {item.label}
                                    </Link>
                                ))}
                            </div>
                        </div>
                        <div className="flex items-center">
                            <button
                                onClick={handleLogout}
                                className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 hover:bg-gray-50 ring-1 ring-inset ring-gray-300"
                            >
                                Sign out
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Page Content */}
            <main className="py-10">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    {headerTitle && (
                        <header className="mb-8">
                            <p className="text-sm uppercase tracking-wide text-indigo-600">Admin Console</p>
                            <h1 className="mt-2 text-3xl font-semibold text-gray-900">{headerTitle}</h1>
                            {headerSubtitle && <p className="mt-1 text-sm text-gray-500">{headerSubtitle}</p>}
                        </header>
                    )}
                    {children}
                </div>
            </main>
        </div>
    );
}
