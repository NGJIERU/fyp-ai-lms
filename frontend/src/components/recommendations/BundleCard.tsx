"use client";

import { useState } from "react";
import { 
  PlayCircleIcon, 
  DocumentTextIcon, 
  CodeBracketIcon, 
  BookOpenIcon,
  GlobeAltIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ArrowTopRightOnSquareIcon
} from "@heroicons/react/24/outline";

interface BundleMaterial {
  id: number;
  title: string;
  url: string;
  source: string;
  type: string;
  similarity_score?: number;
  quality_score?: number;
}

interface BundleCardProps {
  weekNumber: number;
  topic: string;
  summary: string;
  materials: BundleMaterial[];
  onMaterialClick: (materialId: number) => void;
}

function getMaterialIcon(type: string, source: string) {
  const iconClass = "w-4 h-4";
  
  const sourceLower = source.toLowerCase();
  if (sourceLower.includes("youtube")) {
    return <PlayCircleIcon className={`${iconClass} text-red-500`} />;
  }
  if (sourceLower.includes("github")) {
    return <CodeBracketIcon className={`${iconClass} text-gray-700`} />;
  }
  if (sourceLower.includes("arxiv")) {
    return <DocumentTextIcon className={`${iconClass} text-orange-500`} />;
  }
  
  const typeLower = type.toLowerCase();
  if (typeLower === "video") {
    return <PlayCircleIcon className={`${iconClass} text-red-500`} />;
  }
  if (typeLower === "article" || typeLower === "paper") {
    return <DocumentTextIcon className={`${iconClass} text-blue-500`} />;
  }
  if (typeLower === "repository" || typeLower === "code") {
    return <CodeBracketIcon className={`${iconClass} text-purple-500`} />;
  }
  if (typeLower === "course" || typeLower === "tutorial") {
    return <BookOpenIcon className={`${iconClass} text-green-500`} />;
  }
  
  return <GlobeAltIcon className={`${iconClass} text-gray-400`} />;
}

function getSourceBadgeColor(source: string): string {
  const sourceLower = source.toLowerCase();
  if (sourceLower.includes("youtube")) return "bg-red-50 text-red-600";
  if (sourceLower.includes("github")) return "bg-gray-100 text-gray-600";
  if (sourceLower.includes("arxiv")) return "bg-orange-50 text-orange-600";
  if (sourceLower.includes("manual")) return "bg-indigo-50 text-indigo-600";
  return "bg-gray-50 text-gray-500";
}

export default function BundleCard({
  weekNumber,
  topic,
  summary,
  materials,
  onMaterialClick,
}: BundleCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  // Count materials by type
  const typeCounts = materials.reduce((acc, m) => {
    const source = m.source.toLowerCase();
    if (source.includes("youtube")) acc.video++;
    else if (source.includes("arxiv")) acc.paper++;
    else if (source.includes("github")) acc.code++;
    else acc.other++;
    return acc;
  }, { video: 0, paper: 0, code: 0, other: 0 });

  return (
    <div className="rounded-xl border-2 border-gray-100 bg-white overflow-hidden hover:border-indigo-200 transition-colors">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-bold text-sm">
            W{weekNumber}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">{topic}</h3>
            <div className="flex items-center gap-2 mt-1">
              {typeCounts.video > 0 && (
                <span className="inline-flex items-center gap-1 text-xs text-red-500">
                  <PlayCircleIcon className="w-3.5 h-3.5" />
                  {typeCounts.video}
                </span>
              )}
              {typeCounts.paper > 0 && (
                <span className="inline-flex items-center gap-1 text-xs text-orange-500">
                  <DocumentTextIcon className="w-3.5 h-3.5" />
                  {typeCounts.paper}
                </span>
              )}
              {typeCounts.code > 0 && (
                <span className="inline-flex items-center gap-1 text-xs text-gray-600">
                  <CodeBracketIcon className="w-3.5 h-3.5" />
                  {typeCounts.code}
                </span>
              )}
              {typeCounts.other > 0 && (
                <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                  <GlobeAltIcon className="w-3.5 h-3.5" />
                  {typeCounts.other}
                </span>
              )}
              <span className="text-xs text-gray-400">•</span>
              <span className="text-xs text-gray-500">{materials.length} resources</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronUpIcon className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDownIcon className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Summary */}
          <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-100">
            <p className="text-xs text-indigo-700 leading-relaxed">
              📖 {summary}
            </p>
          </div>

          {/* Materials List */}
          <div className="space-y-2">
            {materials.map((material) => (
              <a
                key={material.id}
                href={material.url}
                target="_blank"
                rel="noreferrer"
                onClick={() => onMaterialClick(material.id)}
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:border-indigo-200 hover:bg-indigo-50/50 transition-all group"
              >
                <div className="p-1.5 rounded-md bg-gray-50 group-hover:bg-white transition-colors">
                  {getMaterialIcon(material.type, material.source)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate group-hover:text-indigo-700 transition-colors">
                    {material.title}
                  </p>
                  <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium mt-1 ${getSourceBadgeColor(material.source)}`}>
                    {material.source}
                  </span>
                </div>
                
                <ArrowTopRightOnSquareIcon className="w-4 h-4 text-gray-300 group-hover:text-indigo-500 transition-colors" />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
