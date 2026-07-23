import Link from 'next/link'
import { ArrowRight, ShieldCheck } from 'lucide-react'
import { TriageSignal } from '@/types/tray'
import { HealthBadge } from './HealthBadge'
import { SourceBadge } from './SourceBadge'

interface TriageQueueProps {
  signals: TriageSignal[]
}

export function TriageQueue({ signals }: TriageQueueProps) {
  return (
    <section
      aria-labelledby="triage-heading"
      className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm"
    >
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div>
          <h2 id="triage-heading" className="text-lg font-semibold text-slate-950">
            Triage queue
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Ranked by operational blast radius
          </p>
        </div>
        <span className="font-mono text-sm text-slate-500">
          {signals.length} actionable
        </span>
      </div>

      {signals.length === 0 ? (
        <div className="flex flex-col items-center px-6 py-12 text-center">
          <ShieldCheck aria-hidden="true" className="h-8 w-8 text-emerald-500" />
          <h3 className="mt-3 font-semibold text-slate-900">Queue is clear</h3>
          <p className="mt-1 max-w-md text-sm text-slate-500">
            No instances currently need operator attention.
          </p>
        </div>
      ) : (
        <ol className="divide-y divide-slate-100">
          {signals.map((signal) => (
            <li key={`${signal.kind}-${signal.instance_id}`} className="px-5 py-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <HealthBadge status={signal.severity} />
                    <SourceBadge source={signal.source} />
                    <span className="font-mono text-xs text-slate-400">
                      {signal.instance_id}
                    </span>
                  </div>
                  <h3 className="mt-2 font-semibold text-slate-900">
                    {signal.title}
                  </h3>
                  <p className="mt-1 text-sm text-slate-600">{signal.reason}</p>
                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                    <span>{signal.users_at_risk} users at risk</span>
                    <span>{signal.executions_at_risk} executions at risk</span>
                    <span>Blast radius {signal.blast_radius}</span>
                  </div>
                </div>
                <Link
                  href={`/internal/tray/instances/${encodeURIComponent(
                    signal.instance_id
                  )}`}
                  className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-indigo-600 hover:text-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  Inspect
                  <ArrowRight aria-hidden="true" className="h-4 w-4" />
                </Link>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
