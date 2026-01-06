"use client";

import { useState } from "react";
import { 
  PlayCircleIcon, 
  DocumentTextIcon, 
  CodeBracketIcon, 
  BookOpenIcon,
  GlobeAltIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  CheckIcon,
  ArrowTopRightOnSquareIcon
} from "@heroicons/react/24/outline";
import { HandThumbUpIcon as HandThumbUpSolid } from "@heroicons/react/24/solid";

interface Material {
  id: number;
  title: string;
  url: string;
  source: string;
  type: string;
}

interface RecommendationCardProps {
  material: Material;
  weekNumber: number;
  topic: string;
  reasons: string[];
  personalizedScore: number;
  similarityScore: number;
  qualityScore: number;
  isLiked?: boolean;
  ratingInFlight?: boolean;
  ratings?: { upvotes: number; downvotes: number };
  onRate: (materialId: number, score: number) => void;
  onMaterialClick: (materialId: number) => void;
}

function getMaterialIcon(type: string, source: string) {
  const iconClass = "w-5 h-5";
  
  // Check source first for more specific icons
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
  
  // Fall back to type
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
  if (sourceLower.includes("youtube")) return "bg-red-50 text-red-700 border-red-200";
  if (sourceLower.includes("github")) return "bg-gray-100 text-gray-700 border-gray-300";
  if (sourceLower.includes("arxiv")) return "bg-orange-50 text-orange-700 border-orange-200";
  if (sourceLower.includes("manual")) return "bg-indigo-50 text-indigo-700 border-indigo-200";
  return "bg-gray-50 text-gray-600 border-gray-200";
}

function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
  const percentage = Math.round(score * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-16">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-600 w-8 text-right">{percentage}%</span>
    </div>
  );
}

export default function RecommendationCard({
  material,
  weekNumber,
  topic,
  reasons,
  personalizedScore,
  similarityScore,
  qualityScore,
  isLiked = false,
  ratingInFlight = false,
  ratings,
  onRate,
  onMaterialClick,
}: RecommendationCardProps) {
  const [showScores, setShowScores] = useState(false);

  return (
    <div
      className={`group rounded-xl border-2 p-4 transition-all duration-300 hover:shadow-md ${
        isLiked 
          ? "border-green-300 bg-gradient-to-br from-green-50 to-emerald-50" 
          : "border-gray-100 bg-white hover:border-indigo-200"
      }`}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        {/* Material Type Icon */}
        <div className={`flex-shrink-0 p-2 rounded-lg ${isLiked ? "bg-green-100" : "bg-gray-50 group-hover:bg-indigo-50"} transition-colors`}>
          {getMaterialIcon(material.type, material.source)}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h3 className={`font-semibold text-sm leading-tight ${isLiked ? "text-green-900" : "text-gray-900"} line-clamp-2`}>
                {material.title}
              </h3>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getSourceBadgeColor(material.source)}`}>
                  {material.source}
                </span>
                <span className="text-xs text-gray-400">•</span>
                <span className={`text-xs ${isLiked ? "text-green-600" : "text-gray-500"}`}>
                  Week {weekNumber}
                </span>
              </div>
            </div>
            
            {/* Open Link Button */}
            <a
              href={material.url}
              target="_blank"
              rel="noreferrer"
              onClick={() => onMaterialClick(material.id)}
              className={`flex-shrink-0 inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                isLiked 
                  ? "bg-green-600 text-white hover:bg-green-700" 
                  : "bg-indigo-600 text-white hover:bg-indigo-700"
              }`}
            >
              Open
              <ArrowTopRightOnSquareIcon className="w-3.5 h-3.5" />
            </a>
          </div>
          
          {/* Topic */}
          <p className={`text-xs mt-2 ${isLiked ? "text-green-700" : "text-gray-500"}`}>
            📍 {topic}
          </p>
          
          {/* Reasons */}
          <div className={`mt-2 p-2 rounded-lg ${isLiked ? "bg-green-100/50" : "bg-gray-50"}`}>
            <p className={`text-xs leading-relaxed ${isLiked ? "text-green-800" : "text-gray-600"}`}>
              💡 {reasons.join(" ")}
            </p>
          </div>
          
          {/* Score Summary - Collapsible */}
          <div className="mt-3">
            <button
              onClick={() => setShowScores(!showScores)}
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              {showScores ? "Hide scores ▲" : "Show scores ▼"}
            </button>
            
            {showScores && (
              <div className="mt-2 space-y-1.5 animate-in slide-in-from-top-2 duration-200">
                <ScoreBar label="Match" score={personalizedScore} color="bg-indigo-500" />
                <ScoreBar label="Relevance" score={similarityScore} color="bg-blue-500" />
                <ScoreBar label="Quality" score={qualityScore} color="bg-emerald-500" />
              </div>
            )}
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100">
            <button
              type="button"
              disabled={ratingInFlight}
              onClick={() => onRate(material.id, 1)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                isLiked 
                  ? "bg-green-600 text-white shadow-sm" 
                  : "border border-gray-200 text-gray-600 hover:border-green-300 hover:bg-green-50 hover:text-green-700"
              }`}
            >
              {isLiked ? (
                <>
                  <CheckIcon className="w-4 h-4" />
                  Saved
                </>
              ) : (
                <>
                  <HandThumbUpIcon className="w-4 h-4" />
                  Helpful
                </>
              )}
            </button>
            
            <button
              type="button"
              disabled={ratingInFlight}
              onClick={() => onRate(material.id, -1)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-semibold text-gray-600 hover:border-red-300 hover:bg-red-50 hover:text-red-700 transition-all"
            >
              <HandThumbDownIcon className="w-4 h-4" />
              Not for me
            </button>
            
            {ratings && (ratings.upvotes > 0 || ratings.downvotes > 0) && (
              <span className="ml-auto text-xs text-gray-400">
                {ratings.upvotes > 0 && <span className="text-green-500">{ratings.upvotes}↑</span>}
                {ratings.upvotes > 0 && ratings.downvotes > 0 && " · "}
                {ratings.downvotes > 0 && <span className="text-red-400">{ratings.downvotes}↓</span>}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
