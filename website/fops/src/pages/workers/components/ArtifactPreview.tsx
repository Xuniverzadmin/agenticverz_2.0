// ArtifactPreview Component - Real-Time Artifact Preview Panel
// Shows live preview of generated artifacts (HTML, Markdown, JSON, etc.)
// Creates the "wow moment" as users watch content assemble in real-time

import { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Code,
  Eye,
  Copy,
  Download,
  Maximize2,
  Minimize2,
  FileCode,
  FileJson,
  Globe,
  CheckCircle,
} from 'lucide-react';
import type { ArtifactEvent } from '@/types/worker';
import clsx from 'clsx';

interface ArtifactContent {
  name: string;
  type: string;
  content: string;
  stage_id: string;
  timestamp?: string;
}

interface ArtifactPreviewProps {
  artifacts: ArtifactEvent[];
  artifactContents: Record<string, ArtifactContent>;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

const ARTIFACT_ICONS: Record<string, React.ReactNode> = {
  html: <Globe className="w-4 h-4" />,
  md: <FileText className="w-4 h-4" />,
  json: <FileJson className="w-4 h-4" />,
  txt: <FileText className="w-4 h-4" />,
  css: <FileCode className="w-4 h-4" />,
  js: <Code className="w-4 h-4" />,
};

const ARTIFACT_COLORS: Record<string, string> = {
  html: 'text-orange-500 bg-orange-100 dark:bg-orange-900/30',
  md: 'text-blue-500 bg-blue-100 dark:bg-blue-900/30',
  json: 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/30',
  txt: 'text-gray-500 bg-gray-100 dark:bg-gray-700',
  css: 'text-pink-500 bg-pink-100 dark:bg-pink-900/30',
  js: 'text-green-500 bg-green-100 dark:bg-green-900/30',
};

function MarkdownRenderer({ content }: { content: string }) {
  // Simple markdown rendering - can be enhanced with a full library
  const lines = content.split('\n');

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      {lines.map((line, i) => {
        // Headers
        if (line.startsWith('### ')) {
          return <h3 key={i} className="text-lg font-semibold mt-4 mb-2">{line.slice(4)}</h3>;
        }
        if (line.startsWith('## ')) {
          return <h2 key={i} className="text-xl font-bold mt-6 mb-3">{line.slice(3)}</h2>;
        }
        if (line.startsWith('# ')) {
          return <h1 key={i} className="text-2xl font-bold mt-6 mb-4">{line.slice(2)}</h1>;
        }
        // Bullet points
        if (line.startsWith('- ') || line.startsWith('* ')) {
          return <li key={i} className="ml-4">{line.slice(2)}</li>;
        }
        // Numbered lists
        if (/^\d+\. /.test(line)) {
          return <li key={i} className="ml-4 list-decimal">{line.replace(/^\d+\. /, '')}</li>;
        }
        // Code blocks
        if (line.startsWith('```')) {
          return null; // Skip code fence markers
        }
        // Bold text (simple)
        if (line.includes('**')) {
          const parts = line.split('**');
          return (
            <p key={i} className="my-1">
              {parts.map((part, j) => (
                j % 2 === 1 ? <strong key={j}>{part}</strong> : part
              ))}
            </p>
          );
        }
        // Empty lines
        if (!line.trim()) {
          return <br key={i} />;
        }
        // Regular paragraphs
        return <p key={i} className="my-1">{line}</p>;
      })}
    </div>
  );
}

function HtmlPreview({ content }: { content: string }) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (iframeRef.current) {
      const doc = iframeRef.current.contentDocument;
      if (doc) {
        doc.open();
        doc.write(content);
        doc.close();
      }
    }
  }, [content]);

  return (
    <iframe
      ref={iframeRef}
      className="w-full h-full border-0 bg-white"
      sandbox="allow-same-origin allow-scripts"
      title="HTML Preview"
    />
  );
}

function JsonPreview({ content }: { content: string }) {
  let formatted = content;
  try {
    const parsed = JSON.parse(content);
    formatted = JSON.stringify(parsed, null, 2);
  } catch {
    // Keep original if not valid JSON
  }

  return (
    <pre className="text-xs font-mono overflow-auto p-4 bg-gray-900 text-gray-100 rounded">
      <code>{formatted}</code>
    </pre>
  );
}

function CodePreview({ content, language }: { content: string; language: string }) {
  return (
    <pre className="text-xs font-mono overflow-auto p-4 bg-gray-900 text-gray-100 rounded">
      <code className={`language-${language}`}>{content}</code>
    </pre>
  );
}

export function ArtifactPreview({
  artifacts,
  artifactContents,
  isExpanded = false,
  onToggleExpand,
}: ArtifactPreviewProps) {
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'preview' | 'source'>('preview');
  const [copied, setCopied] = useState(false);

  // Auto-select first artifact
  useEffect(() => {
    if (artifacts.length > 0 && !selectedArtifact) {
      const key = `${artifacts[0].artifact_name}.${artifacts[0].artifact_type}`;
      setSelectedArtifact(key);
    }
  }, [artifacts, selectedArtifact]);

  // Auto-select newest artifact when it's created
  useEffect(() => {
    if (artifacts.length > 0) {
      const latest = artifacts[artifacts.length - 1];
      const key = `${latest.artifact_name}.${latest.artifact_type}`;
      if (artifactContents[key]) {
        setSelectedArtifact(key);
      }
    }
  }, [artifacts.length, artifactContents]);

  const currentContent = selectedArtifact ? artifactContents[selectedArtifact] : null;

  const handleCopy = async () => {
    if (currentContent) {
      await navigator.clipboard.writeText(currentContent.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (currentContent) {
      const blob = new Blob([currentContent.content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = selectedArtifact || 'artifact.txt';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const renderPreview = () => {
    if (!currentContent) {
      return (
        <div className="flex items-center justify-center h-full text-gray-400">
          <div className="text-center">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Select an artifact to preview</p>
          </div>
        </div>
      );
    }

    if (viewMode === 'source') {
      return <CodePreview content={currentContent.content} language={currentContent.type} />;
    }

    switch (currentContent.type) {
      case 'html':
        return <HtmlPreview content={currentContent.content} />;
      case 'md':
        return (
          <div className="p-4 overflow-auto h-full">
            <MarkdownRenderer content={currentContent.content} />
          </div>
        );
      case 'json':
        return <JsonPreview content={currentContent.content} />;
      default:
        return <CodePreview content={currentContent.content} language={currentContent.type} />;
    }
  };

  return (
    <div className={clsx(
      'h-full flex flex-col bg-white dark:bg-gray-800 rounded-lg overflow-hidden',
      isExpanded && 'fixed inset-4 z-50 shadow-2xl'
    )}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-cyan-500" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Artifact Preview
          </h3>
          {artifacts.length > 0 && (
            <span className="px-2 py-0.5 text-xs bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 rounded-full">
              {artifacts.length} {artifacts.length === 1 ? 'artifact' : 'artifacts'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {currentContent && (
            <>
              <button
                onClick={() => setViewMode(viewMode === 'preview' ? 'source' : 'preview')}
                className={clsx(
                  'p-1.5 rounded text-xs flex items-center gap-1',
                  viewMode === 'source'
                    ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                )}
                title={viewMode === 'preview' ? 'View Source' : 'View Preview'}
              >
                {viewMode === 'preview' ? <Code className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={handleCopy}
                className="p-1.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600"
                title="Copy to clipboard"
              >
                {copied ? <CheckCircle className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={handleDownload}
                className="p-1.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600"
                title="Download"
              >
                <Download className="w-3.5 h-3.5" />
              </button>
            </>
          )}
          {onToggleExpand && (
            <button
              onClick={onToggleExpand}
              className="p-1.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600"
              title={isExpanded ? 'Minimize' : 'Maximize'}
            >
              {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </div>

      {/* Artifact Tabs */}
      {artifacts.length > 0 && (
        <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
          <div className="flex items-center gap-2">
            {artifacts.map((artifact) => {
              const key = `${artifact.artifact_name}.${artifact.artifact_type}`;
              const hasContent = !!artifactContents[key];
              return (
                <button
                  key={key}
                  onClick={() => hasContent && setSelectedArtifact(key)}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap',
                    selectedArtifact === key
                      ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                      : hasContent
                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                      : 'bg-gray-50 dark:bg-gray-800 text-gray-400 dark:text-gray-500 animate-pulse'
                  )}
                  disabled={!hasContent}
                >
                  <span className={clsx('p-0.5 rounded', ARTIFACT_COLORS[artifact.artifact_type] || 'bg-gray-200')}>
                    {ARTIFACT_ICONS[artifact.artifact_type] || <FileText className="w-3 h-3" />}
                  </span>
                  {artifact.artifact_name}
                  {!hasContent && <span className="text-xs">(loading...)</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Preview Area */}
      <div className="flex-1 overflow-hidden">
        {artifacts.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <Sparkles className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">Artifacts will appear here as they are generated</p>
              <p className="text-xs mt-1 text-gray-500">Watch the magic happen in real-time</p>
            </div>
          </div>
        ) : (
          renderPreview()
        )}
      </div>

      {/* Footer with artifact info */}
      {currentContent && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between text-xs text-gray-500">
          <span>
            Stage: <span className="font-medium">{currentContent.stage_id}</span>
          </span>
          <span>
            {currentContent.content.length.toLocaleString()} characters
          </span>
        </div>
      )}
    </div>
  );
}

// Sparkles icon for empty state
function Sparkles({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  );
}
