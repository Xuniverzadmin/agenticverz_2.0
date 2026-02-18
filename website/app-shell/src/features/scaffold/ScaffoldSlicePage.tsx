/**
 * ScaffoldSlicePage
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console
 * Role: Domain/subpage scaffold renderer with contract metadata and live fetch probe.
 */

import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { buildRequestPath, getSlice } from './scaffoldCatalog';

interface ProbeResult {
  status: number;
  contentType: string;
  isJson: boolean;
  bodyPreview: string;
}

export default function ScaffoldSlicePage() {
  const { domain, subpage } = useParams();
  const slice = useMemo(() => getSlice(domain, subpage), [domain, subpage]);

  const [loading, setLoading] = useState(false);
  const [probe, setProbe] = useState<ProbeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slice) {
      setProbe(null);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const requestPath = buildRequestPath(slice);

    async function runProbe() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(requestPath, {
          credentials: 'include',
          headers: { Accept: 'application/json', ...(slice.probeHeaders ?? {}) },
        });
        const contentType = response.headers.get('content-type') ?? '';
        const isJson = contentType.includes('application/json');
        const body = isJson ? JSON.stringify(await response.json(), null, 2) : await response.text();
        if (!cancelled) {
          setProbe({
            status: response.status,
            contentType,
            isJson,
            bodyPreview: body.slice(0, 3000),
          });
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to probe scaffold endpoint');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    runProbe();
    return () => {
      cancelled = true;
    };
  }, [slice]);

  if (!slice) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
        <div className="max-w-4xl mx-auto rounded-lg border border-red-800/50 bg-red-950/20 p-4">
          <h1 className="text-lg font-semibold">Scaffold Route Not Found</h1>
          <p className="mt-2 text-sm text-gray-300">
            No scaffold is registered for <code>/page/{domain}/{subpage}</code>.
          </p>
          <Link className="inline-block mt-4 text-blue-300 hover:underline" to="/page">
            Back to scaffold index
          </Link>
        </div>
      </div>
    );
  }

  const requestPath = buildRequestPath(slice);
  const htmlFallbackDetected = probe && !probe.isJson && probe.bodyPreview.includes('<!DOCTYPE html>');

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">{slice.title}</h1>
          <Link className="text-blue-300 hover:underline" to="/page">
            All scaffold pages
          </Link>
        </div>

        <div className="mt-4 rounded-lg border border-gray-700 bg-gray-800/30 p-4 text-sm">
          <div><span className="text-gray-400">PR:</span> {slice.pr}</div>
          <div><span className="text-gray-400">Route:</span> <code>/page/{slice.domain}/{slice.subpage}</code></div>
          <div><span className="text-gray-400">Facade:</span> <code>{requestPath}</code></div>
          <div><span className="text-gray-400">Contract:</span> <code>{slice.contractDoc}</code></div>
          {slice.preflightReferencePath && (
            <div><span className="text-gray-400">Preflight reference:</span> <code>{slice.preflightReferencePath}</code></div>
          )}
          {slice.legacyReferencePath && (
            <div><span className="text-gray-400">Legacy reference:</span> <code>{slice.legacyReferencePath}</code></div>
          )}
        </div>

        <div className="mt-4 rounded-lg border border-gray-700 bg-gray-800/30 p-4">
          <h2 className="text-base font-medium">Data Probe</h2>
          <p className="text-xs text-gray-400 mt-1">
            Probe executes the mapped facade endpoint to scaffold PR data display on this page.
          </p>

          {loading && <p className="mt-3 text-sm text-gray-300">Loading probe result...</p>}
          {error && <p className="mt-3 text-sm text-red-300">Probe error: {error}</p>}

          {probe && (
            <div className="mt-3">
              <div className="text-sm">
                <span className="text-gray-400">HTTP:</span> {probe.status}
              </div>
              <div className="text-sm">
                <span className="text-gray-400">Content-Type:</span> {probe.contentType || 'unknown'}
              </div>
              {htmlFallbackDetected && (
                <div className="mt-2 rounded border border-yellow-700/60 bg-yellow-900/20 p-2 text-xs text-yellow-200">
                  HTML fallback detected. This usually means the stagetest gateway is not proxying this facade path yet.
                </div>
              )}
              <pre className="mt-3 max-h-[480px] overflow-auto rounded bg-gray-950 p-3 text-xs text-gray-200">
                {probe.bodyPreview || '(empty response body)'}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
