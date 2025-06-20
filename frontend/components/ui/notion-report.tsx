'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Components } from 'react-markdown';

interface NotionReportProps {
  content: string;
}

export function NotionReport({ content }: NotionReportProps) {
  // Custom components for Notion-style rendering
  const components: Components = {
    // Custom heading styles with emojis
    h1: ({ children }) => (
      <h1 className="text-4xl font-bold text-gray-900 mb-8 pb-4 border-b border-gray-200">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-2xl font-semibold text-gray-800 mb-6 mt-8 pb-2 border-b border-gray-100 flex items-center gap-2">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-xl font-medium text-gray-700 mb-4 mt-6 flex items-center gap-2">
        {children}
      </h3>
    ),
    
    // Enhanced paragraph styling with competitor card detection
    p: ({ children }) => {
      const content = children?.toString() || '';
      
      // Check if this is a competitor card (starts with **N. Product Name**)
      const isCompetitorCard = /^\*\*\d+\.\s/.test(content);
      
      if (isCompetitorCard) {
        // Determine competitor strength based on emoji
        let cardClass = 'competitor-card';
        if (content.includes('🔥')) cardClass += ' strong';
        else if (content.includes('💪')) cardClass += ' moderate';
        else if (content.includes('📈')) cardClass += ' emerging';
        
        return (
          <p className={`text-gray-600 leading-relaxed mb-4 text-base ${cardClass}`}>
            {children}
          </p>
        );
      }
      
      // Special handling for key-value pairs (like **Key:** Value)
      if (content.includes('**') && content.includes(':')) {
        return (
          <p className="text-gray-600 leading-relaxed mb-3 text-base flex flex-wrap items-baseline gap-1">
            {children}
          </p>
        );
      }
      
      return (
        <p className="text-gray-600 leading-relaxed mb-4 text-base">
          {children}
        </p>
      );
    },
    
    // Strong text styling
    strong: ({ children }) => (
      <strong className="font-semibold text-gray-800">
        {children}
      </strong>
    ),
    
    // List styling
    ul: ({ children }) => (
      <ul className="space-y-2 mb-4 ml-4">
        {children}
      </ul>
    ),
    li: ({ children }) => (
      <li className="text-gray-600 leading-relaxed flex items-start">
        <span className="text-blue-500 mr-2 mt-1">•</span>
        <span>{children}</span>
      </li>
    ),
    
    // Table styling for competitor comparison
    table: ({ children }) => (
      <div className="overflow-x-auto mb-6 rounded-lg border border-gray-200">
        <table className="w-full border-collapse bg-white">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="bg-gray-50">
        {children}
      </thead>
    ),
    th: ({ children }) => (
      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b border-gray-200">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="px-4 py-3 text-sm text-gray-600 border-b border-gray-100">
        {children}
      </td>
    ),
    tr: ({ children }) => (
      <tr className="hover:bg-gray-25 transition-colors">
        {children}
      </tr>
    ),
    
    // Code styling (for inline code like ASINs)
    code: ({ children }) => (
      <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">
        {children}
      </code>
    ),
    
    // Blockquote styling
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-500 pl-4 py-2 bg-blue-50 mb-4 italic text-gray-700">
        {children}
      </blockquote>
    ),
    
    // Horizontal rule styling
    hr: () => (
      <hr className="my-8 border-t border-gray-200" />
    )
  };

  // Process content to enhance Notion-style formatting
  const processContent = (content: string): string => {
    return content
      // Add better spacing around sections
      .replace(/^(#{1,3})\s+([^#\n]+)/gm, (match, hashes, title) => {
        // Keep emoji headers as-is
        return `${hashes} ${title}`;
      })
      // Enhance bullet points with better formatting
      .replace(/^(\s*)[-*]\s+(.+)/gm, '$1• $2')
      // Add spacing around tables
      .replace(/(\|.*\|)\n(\|.*\|)/g, '$1\n\n$2')
      // Better formatting for key-value pairs
      .replace(/\*\*(.*?):\*\*\s*(.+)/g, '**$1:** $2')
      // Add line breaks for better readability
      .replace(/(\*\*[^*]+:\*\*[^\n]+)\n(?!\*\*|\n|#)/g, '$1  \n');
  };

  const processedContent = processContent(content);

  return (
    <div className="notion-report">
      <style jsx global>{`
        .notion-report {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
          line-height: 1.6;
        }
        
        /* Enhanced section spacing */
        .notion-report > div > * + * {
          margin-top: 1.5rem;
        }
        
        /* Better typography hierarchy */
        .notion-report h1 {
          font-size: 2.25rem;
          font-weight: 700;
          color: #111827;
          margin-bottom: 2rem;
          padding-bottom: 1rem;
          border-bottom: 2px solid #e5e7eb;
        }
        
        .notion-report h2 {
          font-size: 1.5rem;
          font-weight: 600;
          color: #374151;
          margin-top: 2rem;
          margin-bottom: 1rem;
          padding-bottom: 0.5rem;
          border-bottom: 1px solid #f3f4f6;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .notion-report h3 {
          font-size: 1.25rem;
          font-weight: 500;
          color: #4b5563;
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        /* Table styling improvements */
        .notion-report table {
          width: 100%;
          border-collapse: collapse;
          margin: 1.5rem 0;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          background: white;
        }
        
        .notion-report thead {
          background: #f8fafc;
        }
        
        .notion-report th {
          padding: 12px 16px;
          text-align: left;
          font-weight: 600;
          color: #374151;
          border-bottom: 2px solid #e5e7eb;
          font-size: 0.875rem;
          text-transform: uppercase;
          letter-spacing: 0.025em;
        }
        
        .notion-report td {
          padding: 12px 16px;
          color: #4b5563;
          border-bottom: 1px solid #f3f4f6;
          font-size: 0.875rem;
        }
        
        .notion-report tbody tr:hover {
          background: #f8fafc;
        }
        
        /* Special cell styling */
        .notion-report td:has-text("🎯") {
          font-weight: 600;
          color: #059669;
        }
        
        .notion-report td:has-text("⭐") {
          color: #f59e0b;
        }
        
        /* Enhanced list styling */
        .notion-report ul {
          list-style: none;
          padding-left: 0;
          margin: 1rem 0;
        }
        
        .notion-report li {
          position: relative;
          padding-left: 1.5rem;
          margin-bottom: 0.5rem;
          color: #4b5563;
          line-height: 1.6;
        }
        
        .notion-report li::before {
          content: "•";
          color: #3b82f6;
          font-weight: bold;
          position: absolute;
          left: 0;
          top: 0;
        }
        
        /* Competitor card styling - add custom class via React component */
        .notion-report .competitor-card {
          background: #f8fafc;
          border-left: 4px solid #3b82f6;
          padding: 1rem;
          margin: 1rem 0;
          border-radius: 0 8px 8px 0;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          line-height: 1.7;
        }
        
        .notion-report .competitor-card.strong {
          border-left-color: #ef4444;
        }
        
        .notion-report .competitor-card.moderate {
          border-left-color: #f59e0b;
        }
        
        .notion-report .competitor-card.emerging {
          border-left-color: #10b981;
        }
        
        /* Code and emphasis styling */
        .notion-report strong {
          font-weight: 600;
          color: #111827;
        }
        
        .notion-report code {
          background: #f3f4f6;
          color: #374151;
          padding: 2px 6px;
          border-radius: 4px;
          font-family: 'SF Mono', Monaco, Inconsolata, 'Roboto Mono', Consolas, 'Courier New', monospace;
          font-size: 0.875em;
        }
        
        /* Horizontal rule styling */
        .notion-report hr {
          border: none;
          height: 1px;
          background: #e5e7eb;
          margin: 2rem 0;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
          .notion-report table {
            font-size: 0.75rem;
          }
          
          .notion-report th,
          .notion-report td {
            padding: 8px 12px;
          }
          
          .notion-report h1 {
            font-size: 1.875rem;
          }
          
          .notion-report h2 {
            font-size: 1.25rem;
          }
          
          .notion-report h3 {
            font-size: 1.125rem;
          }
        }
      `}</style>
      
      <div className="space-y-4">
        <ReactMarkdown components={components}>
          {processedContent}
        </ReactMarkdown>
      </div>
    </div>
  );
}