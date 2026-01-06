"use client";

import { useState } from "react";
import {
  FunnelIcon,
  ArrowsUpDownIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

export type SortOption = "relevance" | "quality" | "recent";
export type FilterOption = "all" | "youtube" | "arxiv" | "github" | "manual";

interface RecommendationFiltersProps {
  sortBy: SortOption;
  filterBy: FilterOption;
  onSortChange: (sort: SortOption) => void;
  onFilterChange: (filter: FilterOption) => void;
  totalCount: number;
  filteredCount: number;
}

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "relevance", label: "Most Relevant" },
  { value: "quality", label: "Highest Quality" },
  { value: "recent", label: "Most Recent" },
];

const FILTER_OPTIONS: { value: FilterOption; label: string; color: string }[] = [
  { value: "all", label: "All Sources", color: "bg-gray-100 text-gray-700" },
  { value: "youtube", label: "YouTube", color: "bg-red-50 text-red-700" },
  { value: "arxiv", label: "arXiv", color: "bg-orange-50 text-orange-700" },
  { value: "github", label: "GitHub", color: "bg-gray-100 text-gray-700" },
  { value: "manual", label: "Uploaded", color: "bg-indigo-50 text-indigo-700" },
];

export default function RecommendationFilters({
  sortBy,
  filterBy,
  onSortChange,
  onFilterChange,
  totalCount,
  filteredCount,
}: RecommendationFiltersProps) {
  const [showFilters, setShowFilters] = useState(false);

  const activeFilter = FILTER_OPTIONS.find((f) => f.value === filterBy);
  const hasActiveFilter = filterBy !== "all";

  return (
    <div className="mb-4">
      {/* Compact Controls */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {/* Sort Dropdown */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => onSortChange(e.target.value as SortOption)}
              className="appearance-none pl-8 pr-8 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent cursor-pointer"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <ArrowsUpDownIcon className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
              hasActiveFilter
                ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                : "bg-white text-gray-700 border-gray-200 hover:border-gray-300"
            }`}
          >
            <FunnelIcon className="w-4 h-4" />
            {hasActiveFilter ? activeFilter?.label : "Filter"}
          </button>

          {/* Clear Filter */}
          {hasActiveFilter && (
            <button
              onClick={() => onFilterChange("all")}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
              title="Clear filter"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Count */}
        <span className="text-xs text-gray-500">
          {filteredCount === totalCount
            ? `${totalCount} items`
            : `${filteredCount} of ${totalCount}`}
        </span>
      </div>

      {/* Expanded Filter Options */}
      {showFilters && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-100 animate-in slide-in-from-top-2 duration-200">
          <p className="text-xs font-medium text-gray-500 mb-2">Filter by source:</p>
          <div className="flex flex-wrap gap-2">
            {FILTER_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onFilterChange(option.value);
                  setShowFilters(false);
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                  filterBy === option.value
                    ? `${option.color} border-current ring-2 ring-offset-1 ring-current/20`
                    : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
