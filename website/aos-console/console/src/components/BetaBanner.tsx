/**
 * BetaBanner - Founder Beta Warning Banner
 *
 * PIN-189 Guardrail: Must appear on ALL console pages during beta.
 *
 * Purpose:
 * - Prevents false confidence in topology
 * - Keeps everyone mentally in beta mode
 * - Explicitly marks route-level separation as TEMPORARY
 *
 * Remove ONLY when:
 * - Beta exit criteria met (PIN-188)
 * - Subdomains deployed and verified
 */

import { AlertTriangle } from 'lucide-react';

export function BetaBanner() {
  return (
    <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2">
      <div className="max-w-7xl mx-auto flex items-center gap-3 text-amber-400 text-sm">
        <AlertTriangle className="w-4 h-4 flex-shrink-0" />
        <span>
          <strong>Founder Beta</strong> — Deployment topology not final.
          Subdomains and isolation will be enforced post-beta.
        </span>
      </div>
    </div>
  );
}
