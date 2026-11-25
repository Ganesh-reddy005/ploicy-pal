"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Copy, Check } from "lucide-react";

interface Citation {
  section_id: string;
  clause_name: string;
  text_snippet: string;
}

interface CitationCardProps {
  citation: Citation;
  index: number;
}

export default function CitationCard({ citation, index }: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(citation.text_snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-gray-50 border border-gray-100 rounded-lg overflow-hidden">
      {/* Citation Header */}
      <div className="w-full px-3 py-2.5 flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 min-w-0 flex-1 text-left hover:opacity-70 transition-opacity"
        >
          <span className="flex items-center justify-center w-5 h-5 bg-gray-200 text-gray-600 rounded text-xs font-medium">
            {index + 1}
          </span>
          <div className="min-w-0">
            <p className="text-xs font-medium text-gray-900 truncate">
              {citation.clause_name || "Unnamed Clause"}
            </p>
            <p className="text-xs text-gray-400 truncate">
              {citation.section_id || "Unknown Section"}
            </p>
          </div>
        </button>
        <div className="flex items-center gap-1 ml-2">
          <button
            onClick={handleCopy}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded transition-colors"
            title="Copy text"
            type="button"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-green-500" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded transition-colors"
            title={isExpanded ? "Collapse" : "Expand"}
            type="button"
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Expandable Content */}
      {isExpanded && (
        <div className="px-3 pb-3 border-t border-gray-100 animate-slide-down">
          <div className="mt-2 p-2.5 bg-white rounded text-xs text-gray-600 whitespace-pre-wrap font-mono leading-relaxed max-h-40 overflow-y-auto">
            {citation.text_snippet}
          </div>
        </div>
      )}
    </div>
  );
}