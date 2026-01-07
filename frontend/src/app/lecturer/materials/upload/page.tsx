"use client";

import { useState, ChangeEvent, FormEvent, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useRequireRole } from "@/hooks/useRequireRole";

type CourseOption = {
    course_id: number;
    course_code: string;
    course_name: string;
};

export default function UploadMaterialPage() {
    const router = useRouter();
    const { loading: authLoading, authorized } = useRequireRole(["lecturer", "super_admin"]);

    const [courses, setCourses] = useState<CourseOption[]>([]);
    const [loadingCourses, setLoadingCourses] = useState(true);

    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [type, setType] = useState("pdf");
    const [courseId, setCourseId] = useState<number | "">("");
    const [weekNumber, setWeekNumber] = useState<number>(1);  // NEW: Week number
    const [file, setFile] = useState<File | null>(null);
    const [url, setUrl] = useState("");  // NEW: URL field

    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);  // NEW: For URL analysis

    useEffect(() => {
        if (authLoading || !authorized) return;
        const token = localStorage.getItem("access_token");
        if (!token) return;

        apiFetch<{ courses: CourseOption[] }>("/api/v1/dashboard/lecturer", {
            headers: { Authorization: `Bearer ${token}` }
        })
            .then((data) => {
                setCourses(data.courses);
                if (data.courses.length > 0) {
                    setCourseId(data.courses[0].course_id);
                }
            })
            .catch(() => setError("Failed to load courses"))
            .finally(() => setLoadingCourses(false));
    }, [authLoading, authorized]);

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files?.[0]) setFile(e.target.files[0]);
    };

    const handleAnalyzeUrl = async () => {
        if (!url.trim()) {
            return setError("Please enter a URL first");
        }

        setIsAnalyzing(true);
        setError(null);
        const token = localStorage.getItem("access_token");

        try {
            const result = await apiFetch<{
                title: string;
                description: string;
                type: string;
                confidence: number;
            }>("/api/v1/lecturer/materials/analyze-url", {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: JSON.stringify({ url: url.trim() }),
            });

            setTitle(result.title);
            setDescription(result.description);
            setType(result.type);
        } catch (err: any) {
            setError(err.message || "Failed to analyze URL");
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();

        // Validate: must have either file OR URL
        if (!file && !url.trim()) {
            return setError("Please either upload a file or provide a URL");
        }
        if (file && url.trim()) {
            return setError("Please provide either a file OR a URL, not both");
        }
        if (!courseId) {
            return setError("Please select a course");
        }

        setIsSubmitting(true);
        setError(null);
        const token = localStorage.getItem("access_token");

        const form = new FormData();
        form.append("title", title);
        form.append("description", description);
        form.append("type", type);
        form.append("course_id", String(courseId));
        form.append("week_number", String(weekNumber));  // NEW: Include week number

        // Add file OR URL
        if (file) {
            form.append("file", file);
        } else if (url.trim()) {
            form.append("url", url.trim());
        }

        try {
            await apiFetch<any>("/api/v1/lecturer/materials/", {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: form,
            });
            router.replace("/lecturer/dashboard");
        } catch (err: any) {
            setError(err.message || "Upload failed");
        } finally {
            setIsSubmitting(false);
        }
    };

    if (authLoading || loadingCourses) {
        return <div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-500">Loading...</div>;
    }

    if (!authorized) return null;

    return (
        <div className="min-h-screen bg-gray-50 px-4 py-10">
            <div className="mx-auto max-w-2xl px-4 lg:px-8">
                <Link href="/lecturer/dashboard" className="mb-6 inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-800">
                    ← Back to Dashboard
                </Link>

                <div className="rounded-2xl bg-white p-8 shadow-sm border border-gray-100">
                    <header className="mb-8 border-b border-gray-100 pb-6">
                        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Material Management</p>
                        <h1 className="mt-2 text-2xl font-bold text-gray-900">Upload New Material</h1>
                        <p className="mt-1 text-sm text-gray-500">Share lecture notes, assignments, or supplementary videos.</p>
                    </header>

                    {error && (
                        <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-700">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Content Title</label>
                            <input
                                type="text"
                                placeholder="e.g., Week 1 Slides - Introduction"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                            />
                        </div>

                        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Target Course</label>
                                <select
                                    value={courseId}
                                    onChange={(e) => setCourseId(Number(e.target.value))}
                                    className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                >
                                    {courses.map(c => (
                                        <option key={c.course_id} value={c.course_id}>{c.course_code} - {c.course_name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">Week Number</label>
                                <select
                                    value={weekNumber}
                                    onChange={(e) => setWeekNumber(Number(e.target.value))}
                                    className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                >
                                    {Array.from({ length: 14 }, (_, i) => i + 1).map(week => (
                                        <option key={week} value={week}>Week {week}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">Material Type</label>
                                <select
                                    value={type}
                                    onChange={(e) => setType(e.target.value)}
                                    className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                >
                                    <option value="pdf">PDF Document</option>
                                    <option value="ppt">Presentation (PPT)</option>
                                    <option value="video">Video</option>
                                    <option value="article">Article / Reading</option>
                                    <option value="exercise">Exercise / Assignment</option>
                                    <option value="dataset">Dataset</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700">Description</label>
                            <textarea
                                placeholder="Optional details for students..."
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                rows={3}
                                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700">Resource URL (Optional)</label>
                            <div className="mt-1 flex gap-2">
                                <input
                                    type="url"
                                    placeholder="e.g., https://www.youtube.com/watch?v=... or https://example.com/article"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    className="block w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                />
                                <button
                                    type="button"
                                    onClick={handleAnalyzeUrl}
                                    disabled={isAnalyzing || !url.trim()}
                                    className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                                >
                                    {isAnalyzing ? (
                                        <>
                                            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            Analyzing...
                                        </>
                                    ) : (
                                        <>
                                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                            </svg>
                                            Analyze URL
                                        </>
                                    )}
                                </button>
                            </div>
                            <p className="mt-1 text-xs text-gray-500">
                                Click "Analyze URL" to auto-fill title, description, and type using AI
                            </p>
                        </div>

                        <div className="relative">
                            <div className="absolute inset-0 flex items-center" aria-hidden="true">
                                <div className="w-full border-t border-gray-200" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="bg-white px-2 text-gray-500">OR</span>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700">File Attachment</label>
                            <div className="mt-1 flex justify-center rounded-lg border-2 border-dashed border-gray-300 px-6 pt-5 pb-6 hover:bg-gray-50 transition-colors">
                                <div className="space-y-1 text-center">
                                    <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                    <div className="flex text-sm text-gray-600 justify-center">
                                        <label htmlFor="file-upload" className="relative cursor-pointer rounded-md bg-white font-medium text-indigo-600 focus-within:outline-none focus-within:ring-2 focus-within:ring-indigo-500 focus-within:ring-offset-2 hover:text-indigo-500">
                                            <span>Upload a file</span>
                                            <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} />
                                        </label>
                                        <p className="pl-1">or drag and drop</p>
                                    </div>
                                    <p className="text-xs text-gray-500">PDF, PPTX, MP4, DOCX up to 50MB</p>
                                    {file && <p className="text-sm font-medium text-indigo-600 mt-2">Selected: {file.name}</p>}
                                </div>
                            </div>
                        </div>

                        <div className="pt-4">
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="w-full flex justify-center rounded-lg border border-transparent bg-indigo-600 py-3 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-70 disabled:cursor-not-allowed transition-all"
                            >
                                {isSubmitting ? (
                                    <span className="flex items-center gap-2">
                                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Uploading...
                                    </span>
                                ) : "Publish Material"}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
