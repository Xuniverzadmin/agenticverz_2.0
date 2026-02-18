/**
 * ScaffoldCatalogPage
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console
 * Role: Entry page for stagetest scaffold subpages.
 */

import { Link } from 'react-router-dom';
import { SCAFFOLD_SLICES } from './scaffoldCatalog';

function groupByDomain() {
  return SCAFFOLD_SLICES.reduce<Record<string, typeof SCAFFOLD_SLICES>>((acc, slice) => {
    if (!acc[slice.domain]) {
      acc[slice.domain] = [];
    }
    acc[slice.domain].push(slice);
    return acc;
  }, {});
}

export default function ScaffoldCatalogPage() {
  const grouped = groupByDomain();
  const domains = Object.keys(grouped).sort();

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-semibold">Stagetest Scaffold Pages</h1>
        <p className="text-sm text-gray-400 mt-2">
          Contract-first page scaffolds for PR1-PR10 at <code>/page/&lt;domain&gt;/&lt;subpage&gt;</code>.
        </p>

        <div className="mt-6 grid gap-5 md:grid-cols-2">
          {domains.map((domain) => (
            <section key={domain} className="rounded-lg border border-gray-700 bg-gray-800/30 p-4">
              <h2 className="text-lg font-medium capitalize">{domain}</h2>
              <ul className="mt-3 space-y-2">
                {grouped[domain].map((slice) => {
                  const href = `/page/${slice.domain}/${slice.subpage}`;
                  return (
                    <li key={`${slice.pr}-${slice.domain}-${slice.subpage}`}>
                      <Link className="text-blue-300 hover:text-blue-200 hover:underline" to={href}>
                        {slice.pr} - {slice.subpage}
                      </Link>
                      <div className="text-xs text-gray-400">{slice.title}</div>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}

