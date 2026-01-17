"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useRequireRole } from "@/hooks/useRequireRole";

type SyllabusEntry = {
  id: number;
  course_id: number;
  week_number: number;
  topic: string;
  content: string | null;
  version: number;
  is_active: boolean;
  created_by_name: string | null;
};

type CourseInfo = {
  id: number;
  code: string;
  name: string;
};

export default function SyllabusManagementPage() {
  const params = useParams<{ courseId: string }>();
  const courseId = Number(params?.courseId);
  const { loading: authLoading, authorized } = useRequireRole(["lecturer", "super_admin"]);

  const [course, setCourse] = useState<CourseInfo | null>(null);
  const [syllabus, setSyllabus] = useState<SyllabusEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state for adding/editing
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<SyllabusEntry | null>(null);
  const [formData, setFormData] = useState({
    week_number: 1,
    topic: "",
    content: "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (authLoading || !authorized || !courseId) return;
    fetchData();
  }, [authLoading, authorized, courseId]);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      // Fetch course info
      const courseData = await apiFetch<any>(`/api/v1/courses/${courseId}`);
      setCourse({
        id: courseData.id,
        code: courseData.code,
        name: courseData.name,
      });

      // Fetch syllabus
      const syllabusData = await apiFetch<SyllabusEntry[]>(
        `/api/v1/syllabus/?course_id=${courseId}&include_inactive=false`
      );
      setSyllabus(syllabusData);
    } catch (err: any) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  function openAddModal() {
    // Find next available week number
    const usedWeeks = new Set(syllabus.map((s) => s.week_number));
    let nextWeek = 1;
    while (usedWeeks.has(nextWeek) && nextWeek <= 14) {
      nextWeek++;
    }
    setFormData({ week_number: nextWeek, topic: "", content: "" });
    setEditingEntry(null);
    setIsModalOpen(true);
  }

  function openEditModal(entry: SyllabusEntry) {
    setFormData({
      week_number: entry.week_number,
      topic: entry.topic,
      content: entry.content || "",
    });
    setEditingEntry(entry);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingEntry(null);
    setFormData({ week_number: 1, topic: "", content: "" });
  }

  async function handleSave() {
    if (!formData.topic.trim()) {
      setError("Topic is required");
      return;
    }

    // Client-side validation for duplicates
    const trimmedTopic = formData.topic.trim();
    
    // Check for duplicate week (when creating new or changing week number)
    const duplicateWeek = syllabus.find(
      (s) => s.week_number === formData.week_number && s.id !== editingEntry?.id
    );
    if (duplicateWeek) {
      setError(`Week ${formData.week_number} already exists with topic "${duplicateWeek.topic}". Please choose a different week.`);
      return;
    }

    // Check for duplicate topic (when creating new or changing topic)
    const duplicateTopic = syllabus.find(
      (s) => s.topic.toLowerCase() === trimmedTopic.toLowerCase() && s.id !== editingEntry?.id
    );
    if (duplicateTopic) {
      setError(`Topic "${trimmedTopic}" already exists in Week ${duplicateTopic.week_number}. Please use a different topic name.`);
      return;
    }

    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      if (editingEntry) {
        // Update existing
        await apiFetch(`/api/v1/syllabus/${editingEntry.id}`, {
          method: "PUT",
          body: JSON.stringify({
            week_number: formData.week_number,
            topic: trimmedTopic,
            content: formData.content || null,
            change_reason: "Updated via UI",
          }),
        });
        setSuccessMessage("Syllabus entry updated successfully");
      } else {
        // Create new
        await apiFetch(`/api/v1/syllabus/`, {
          method: "POST",
          body: JSON.stringify({
            course_id: courseId,
            week_number: formData.week_number,
            topic: trimmedTopic,
            content: formData.content || null,
            change_reason: "Created via UI",
          }),
        });
        setSuccessMessage("Syllabus entry created successfully");
      }
      closeModal();
      fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(entry: SyllabusEntry) {
    if (!confirm(`Are you sure you want to delete Week ${entry.week_number}: ${entry.topic}?`)) {
      return;
    }

    setError(null);
    setSuccessMessage(null);

    try {
      await apiFetch(`/api/v1/syllabus/${entry.id}`, {
        method: "DELETE",
      });
      setSuccessMessage("Syllabus entry deleted successfully");
      fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to delete");
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="mx-auto max-w-4xl">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto flex max-w-4xl flex-col gap-6">
        {/* Header */}
        <header>
          <Link
            href={`/lecturer/course/${courseId}`}
            className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
          >
            ← Back to Course Analytics
          </Link>
          <h1 className="mt-4 text-3xl font-semibold text-gray-900">Manage Syllabus</h1>
          {course && (
            <p className="mt-1 text-sm text-gray-500">
              {course.code} · {course.name}
            </p>
          )}
        </header>

        {/* Messages */}
        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4">
            <p className="text-sm text-red-600">{error}</p>
            <button onClick={() => setError(null)} className="mt-2 text-xs text-red-500 hover:underline">
              Dismiss
            </button>
          </div>
        )}
        {successMessage && (
          <div className="rounded-lg bg-green-50 border border-green-200 p-4">
            <p className="text-sm text-green-600">{successMessage}</p>
            <button onClick={() => setSuccessMessage(null)} className="mt-2 text-xs text-green-500 hover:underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Add Button */}
        <div className="flex justify-end">
          <button
            onClick={openAddModal}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
          >
            + Add Week
          </button>
        </div>

        {/* Syllabus Table */}
        <section className="rounded-2xl bg-white shadow-sm overflow-hidden">
          {syllabus.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-4xl mb-3">📚</div>
              <p className="text-gray-500">No syllabus entries yet.</p>
              <p className="text-sm text-gray-400 mt-1">Click "Add Week" to create your first entry.</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Week
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Topic
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Content
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {syllabus
                  .sort((a, b) => a.week_number - b.week_number)
                  .map((entry) => (
                    <tr key={entry.id} className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-indigo-100 text-indigo-700 font-semibold text-sm">
                          {entry.week_number}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm font-medium text-gray-900">{entry.topic}</p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-gray-500 truncate max-w-xs">
                          {entry.content || "—"}
                        </p>
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        <button
                          onClick={() => openEditModal(entry)}
                          className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(entry)}
                          className="text-sm font-medium text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          )}
        </section>

        {/* Summary */}
        <p className="text-center text-sm text-gray-400">
          {syllabus.length} week{syllabus.length !== 1 ? "s" : ""} in syllabus
        </p>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingEntry ? "Edit Syllabus Entry" : "Add New Week"}
              </h2>
              <button
                onClick={closeModal}
                className="rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Week Number</label>
                <select
                  value={formData.week_number}
                  onChange={(e) => setFormData({ ...formData, week_number: Number(e.target.value) })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  {Array.from({ length: 14 }, (_, i) => i + 1).map((w) => (
                    <option key={w} value={w}>
                      Week {w}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Topic *</label>
                <input
                  type="text"
                  value={formData.topic}
                  onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                  placeholder="e.g., Introduction to Python"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Content (Optional)</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="Additional description or learning objectives..."
                  rows={4}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 border-t px-6 py-4">
              <button
                onClick={closeModal}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:bg-indigo-400"
              >
                {saving ? "Saving..." : editingEntry ? "Update" : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
