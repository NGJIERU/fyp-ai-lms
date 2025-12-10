import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">
            AI-Powered LMS
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Sign in or create an account to continue
          </p>
        </div>
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          {children}
        </div>
      </div>
    </div>
  );
}
