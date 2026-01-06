"use client";

interface TutorExplanationProps {
  content: string;
}

// Simple markdown-like renderer - no complex section parsing
export default function TutorExplanation({ content }: TutorExplanationProps) {
  return (
    <div className="prose prose-sm max-w-none">
      <div className="text-gray-700 leading-relaxed">
        {renderContent(content)}
      </div>
    </div>
  );
}

function renderContent(text: string): React.ReactNode {
  const elements: React.ReactNode[] = [];
  let key = 0;
  
  // Split content by code blocks first
  const parts = text.split(/(```[\s\S]*?```)/g);
  
  for (const part of parts) {
    if (part.startsWith('```')) {
      // Code block
      const match = part.match(/```(\w*)?\n?([\s\S]*?)```/);
      if (match) {
        const lang = match[1] || 'code';
        const code = match[2] || '';
        elements.push(
          <div key={`code-${key++}`} className="my-4 rounded-lg overflow-hidden not-prose">
            <div className="bg-gray-800 px-3 py-2 flex items-center justify-between">
              <span className="text-xs text-gray-400 font-mono uppercase">{lang}</span>
              <button 
                onClick={() => navigator.clipboard.writeText(code.trim())}
                className="text-xs text-gray-400 hover:text-white transition"
              >
                📋 Copy
              </button>
            </div>
            <pre className="bg-gray-900 p-4 overflow-x-auto m-0">
              <code className="text-sm text-green-400 font-mono">{code.trim()}</code>
            </pre>
          </div>
        );
      }
    } else if (part.trim()) {
      // Regular text - render with formatting
      elements.push(
        <div key={`text-${key++}`} className="mb-4">
          {renderFormattedText(part)}
        </div>
      );
    }
  }
  
  return <>{elements}</>;
}

function renderFormattedText(text: string): React.ReactNode {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let key = 0;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    
    if (!trimmed) {
      // Empty line = paragraph break
      elements.push(<div key={`br-${key++}`} className="h-2" />);
      continue;
    }
    
    // Headers
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={`h4-${key++}`} className="text-base font-semibold text-gray-900 mt-4 mb-2">
          {renderInline(trimmed.slice(4))}
        </h4>
      );
    } else if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={`h3-${key++}`} className="text-lg font-semibold text-gray-900 mt-5 mb-2">
          {renderInline(trimmed.slice(3))}
        </h3>
      );
    } else if (trimmed.startsWith('# ')) {
      elements.push(
        <h2 key={`h2-${key++}`} className="text-xl font-bold text-gray-900 mt-6 mb-3">
          {renderInline(trimmed.slice(2))}
        </h2>
      );
    }
    // Numbered headers like "1. Title"
    else if (/^\d+\.\s+[A-Z]/.test(trimmed) && trimmed.length < 80) {
      const match = trimmed.match(/^(\d+)\.\s+(.+)$/);
      if (match) {
        elements.push(
          <h4 key={`num-${key++}`} className="flex items-center gap-2 text-base font-semibold text-gray-900 mt-5 mb-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold">
              {match[1]}
            </span>
            {renderInline(match[2])}
          </h4>
        );
      }
    }
    // Bullet points
    else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      elements.push(
        <div key={`li-${key++}`} className="flex gap-2 ml-2 my-1">
          <span className="text-indigo-500 mt-1">•</span>
          <span>{renderInline(trimmed.slice(2))}</span>
        </div>
      );
    }
    // Regular paragraph
    else {
      elements.push(
        <p key={`p-${key++}`} className="my-1">
          {renderInline(trimmed)}
        </p>
      );
    }
  }
  
  return <>{elements}</>;
}

function renderInline(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;
  
  // Process inline formatting
  while (remaining.length > 0) {
    // Bold **text**
    const boldMatch = remaining.match(/^(.*?)\*\*([^*]+)\*\*(.*)/);
    if (boldMatch) {
      if (boldMatch[1]) parts.push(renderInlineCode(boldMatch[1], key++));
      parts.push(<strong key={`bold-${key++}`} className="font-semibold text-gray-900">{boldMatch[2]}</strong>);
      remaining = boldMatch[3];
      continue;
    }
    
    // No more bold, process rest for inline code
    parts.push(renderInlineCode(remaining, key++));
    break;
  }
  
  return parts.length > 0 ? <>{parts}</> : text;
}

function renderInlineCode(text: string, baseKey: number): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;
  
  while (remaining.length > 0) {
    const codeMatch = remaining.match(/^(.*?)`([^`]+)`(.*)/);
    if (codeMatch) {
      if (codeMatch[1]) parts.push(<span key={`t-${baseKey}-${key++}`}>{codeMatch[1]}</span>);
      parts.push(
        <code key={`c-${baseKey}-${key++}`} className="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono text-xs">
          {codeMatch[2]}
        </code>
      );
      remaining = codeMatch[3];
      continue;
    }
    
    // No more inline code
    if (remaining) parts.push(<span key={`r-${baseKey}-${key++}`}>{remaining}</span>);
    break;
  }
  
  return parts.length > 0 ? <>{parts}</> : text;
}
