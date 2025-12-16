"use client";

import { useState, ChangeEvent, FormEvent } from "react";
import { apiFetch } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function UploadMaterialPage() {
    const router = useRouter();
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [type, setType] = useState("lecture_notes");
    const [courseId, setCourseId] = useState(0);
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files?.[0]) setFile(e.target.files[0]);
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!file) return setError("Please select a file");
        setIsSubmitting(true);
        const token = localStorage.getItem("access_token");
        const form = new FormData();
        form.append("title", title);
        form.append("description", description);
        form.append("type", type);
        form.append("course_id", String(courseId));
        form.append("file", file);
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

    return (
        <div className="min-h-screen bg-gray-50 px-4 py-10">
            <div className="mx-auto max-w-2xl rounded-xl bg-white p-8 shadow-sm">
                <h1 className="mb-6 text-2xl font-semibold text-gray-900">Upload New Material</h1>
                {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        type="text"
                        placeholder="Title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                        className="w-full rounded border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <textarea
                        placeholder="Description (optional)"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="w-full rounded border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <select
                        value={type}
                        onChange={(e) => setType(e.target.value)}
                        className="w-full rounded border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                        <option value="lecture_notes">Lecture Notes</option>
                        <option value="assignment">Assignment</option>
                        <option value="video">Video</option>
                    </select>
                    <input
                        type="number"
                        placeholder="Course ID"
                        value={courseId || ""}
                        onChange={(e) => setCourseId(parseInt(e.target.value, 10))}
                        required
                        className="w-full rounded border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <input type="file" accept="*/*" onChange={handleFileChange} required className="w-full" />
                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full rounded bg-indigo-600 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                        {isSubmitting ? "Uploading…" : "Upload Material"}
                    </button>
                </form>
            </div>
        </div>
    );
}
