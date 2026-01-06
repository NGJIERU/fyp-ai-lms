"use client";

import { useState, useMemo } from "react";
import { ChevronDownIcon, ChevronRightIcon, BookOpenIcon, LightBulbIcon, CodeBracketIcon, AcademicCapIcon } from "@heroicons/react/24/outline";

interface TutorExplanationProps {
  content: string;
}

interface Section {
  title: string;
  content: string;
  subsections: {
    type: "simple" | "technical" | "example" | "other";
    label: string;
    content: string;
  }[];
}

function parseContent(content: string): Section[] {
  const sections: Section[] = [];
  
  // Split by numbered sections (1. 2. 3. etc)
  const sectionRegex = /(\d+\.\s+[^\n]+)/g;
  const parts = content.split(sectionRegex);
  
  let currentSection: Section | null = null;
  
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i].trim();
    if (!part) continue;
    
    // Check if this is a section header (starts with number)
    if (/^\d+\.\s+/.test(part)) {
      if (currentSection) {
        sections.push(currentSection);
      }
      currentSection = {
        title: part.replace(/^\d+\.\s+/, ""),
        content: "",
        subsections: [],
      };
    } else if (currentSection) {
      // Parse subsections within content
      const lines = part.split("\n");
      let currentSubsection: { type: "simple" | "technical" | "example" | "other"; label: string; content: string } | null = null;
      let buffer = "";
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        
        if (trimmedLine.startsWith("**Simple Explanation") || trimmedLine.startsWith("Simple Explanation:")) {
          if (currentSubsection) currentSection.subsections.push(currentSubsection);
          if (buffer.trim()) currentSection.content += buffer;
          buffer = "";
          currentSubsection = { type: "simple", label: "Simple Explanation", content: "" };
        } else if (trimmedLine.startsWith("**Technical Terms") || trimmedLine.startsWith("Technical Terms:")) {
          if (currentSubsection) currentSection.subsections.push(currentSubsection);
          if (buffer.trim()) currentSection.content += buffer;
          buffer = "";
          currentSubsection = { type: "technical", label: "Technical Terms", content: "" };
        } else if (trimmedLine.startsWith("**Concrete Example") || trimmedLine.startsWith("Concrete Example:")) {
          if (currentSubsection) currentSection.subsections.push(currentSubsection);
          if (buffer.trim()) currentSection.content += buffer;
          buffer = "";
          currentSubsection = { type: "example", label: "Concrete Example", content: "" };
        } else if (currentSubsection) {
          currentSubsection.content += line + "\n";
        } else {
          buffer += line + "\n";
        }
      }
      
      if (currentSubsection) currentSection.subsections.push(currentSubsection);
      if (buffer.trim()) currentSection.content = buffer;
    } else {
      // Content before first numbered section
      if (sections.length === 0 && part.trim()) {
        sections.push({
          title: "Introduction",
          content: part,
          subsections: [],
        });
      }
    }
  }
  
  if (currentSection) {
    sections.push(currentSection);
  }
  
  // If no sections were parsed, return the whole content as one section
  if (sections.length === 0) {
    sections.push({
      title: "Explanation",
      content: content,
      subsections: [],
    });
  }
  
  return sections;
}

function highlightKeyTerms(text: string): React.ReactNode[] {
  // Match **term**: description pattern and bold terms
  const parts: React.ReactNode[] = [];
  const regex = /\*\*([^*]+)\*\*:?\s*/g;
  let lastIndex = 0;
  let match;
  let key = 0;
  
  const cleanText = text.replace(/\*\*/g, "");
  const termRegex = /([A-Z][a-zA-Z\s]+(?:\([^)]+\))?)\s*:/g;
  
  let termMatch;
  let processedText = text;
  const terms: string[] = [];
  
  // Find all bold terms
  while ((match = regex.exec(text)) !== null) {
    terms.push(match[1]);
  }
  
  // If we found terms, highlight them
  if (terms.length > 0) {
    let result = text;
    terms.forEach((term, idx) => {
      const boldPattern = `**${term}**`;
      result = result.replace(boldPattern, `|||TERM_${idx}|||`);
    });
    
    const segments = result.split(/\|\|\|TERM_\d+\|\|\|/);
    
    segments.forEach((segment, idx) => {
      if (segment) {
        parts.push(<span key={key++}>{segment.replace(/\*\*/g, "")}</span>);
      }
      if (idx < terms.length) {
        parts.push(
          <span
            key={key++}
            className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-indigo-100 text-indigo-800 mx-1"
          >
            {terms[idx]}
          </span>
        );
      }
    });
    
    return parts;
  }
  
  return [<span key={0}>{text.replace(/\*\*/g, "")}</span>];
}

function SubsectionIcon({ type }: { type: string }) {
  switch (type) {
    case "simple":
      return <LightBulbIcon className="w-4 h-4 text-yellow-500" />;
    case "technical":
      return <CodeBracketIcon className="w-4 h-4 text-blue-500" />;
    case "example":
      return <BookOpenIcon className="w-4 h-4 text-green-500" />;
    default:
      return <AcademicCapIcon className="w-4 h-4 text-gray-500" />;
  }
}

function SubsectionBadge({ type, label }: { type: string; label: string }) {
  const colors = {
    simple: "bg-yellow-50 text-yellow-700 border-yellow-200",
    technical: "bg-blue-50 text-blue-700 border-blue-200",
    example: "bg-green-50 text-green-700 border-green-200",
    other: "bg-gray-50 text-gray-700 border-gray-200",
  };
  
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${colors[type as keyof typeof colors] || colors.other}`}>
      <SubsectionIcon type={type} />
      {label}
    </span>
  );
}

function AccordionSection({ section, index, defaultOpen = false }: { section: Section; index: number; defaultOpen?: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 text-sm font-bold">
            {index + 1}
          </span>
          <h3 className="font-semibold text-gray-900 text-sm sm:text-base">{section.title}</h3>
        </div>
        {isOpen ? (
          <ChevronDownIcon className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronRightIcon className="w-5 h-5 text-gray-400" />
        )}
      </button>
      
      {isOpen && (
        <div className="px-4 pb-4 space-y-4">
          {/* Main content */}
          {section.content && (
            <p className="text-gray-600 text-sm leading-relaxed pl-11">
              {section.content}
            </p>
          )}
          
          {/* Subsections */}
          {section.subsections.map((sub, subIndex) => (
            <div key={subIndex} className="ml-11 space-y-2">
              <div className="border-l-2 border-gray-200 pl-4 py-2">
                <SubsectionBadge type={sub.type} label={sub.label} />
                <div className="mt-2 text-sm text-gray-600 leading-relaxed">
                  {highlightKeyTerms(sub.content)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function TutorExplanation({ content }: TutorExplanationProps) {
  const sections = useMemo(() => parseContent(content), [content]);
  
  const [allExpanded, setAllExpanded] = useState(false);
  
  return (
    <div className="space-y-4">
      {/* Header with expand/collapse all */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500">{sections.length} topics covered</p>
        <button
          onClick={() => setAllExpanded(!allExpanded)}
          className="text-xs font-medium text-indigo-600 hover:text-indigo-800 transition"
        >
          {allExpanded ? "Collapse All" : "Expand All"}
        </button>
      </div>
      
      {/* Accordion sections */}
      <div className="space-y-3">
        {sections.map((section, index) => (
          <AccordionSection
            key={index}
            section={section}
            index={index}
            defaultOpen={allExpanded || index === 0}
          />
        ))}
      </div>
    </div>
  );
}
