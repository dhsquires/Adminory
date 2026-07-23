import { SourceBadge } from './SourceBadge'
import { TraySource } from '@/types/tray'

const signalLabels: Record<string, string> = {
  expired_token: 'Expired tokens',
  misconfigured: 'Misconfigured',
  version_drift: 'Version drift',
  error_spike: 'Error spikes',
  dead_install: 'Dead installs',
  auth_broken: 'Broken auth',
}

interface SignalGroupsProps {
  counts: Record<string, number>
  source?: TraySource
}

export function SignalGroups({
  counts,
  source = 'official',
}: SignalGroupsProps) {
  const groups = Object.entries(counts).filter(([, count]) => count > 0)

  return (
    <section
      aria-labelledby="signals-heading"
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div className="flex items-center gap-2">
        <h2 id="signals-heading" className="text-lg font-semibold text-slate-950">
          Signal groups
        </h2>
        <SourceBadge source={source} />
      </div>
      <p className="mt-1 text-sm text-slate-500">
        The healthy majority is intentionally omitted.
      </p>

      {groups.length === 0 ? (
        <p className="mt-5 rounded-md bg-slate-50 px-3 py-4 text-sm text-slate-500">
          No active signal groups.
        </p>
      ) : (
        <dl className="mt-4 divide-y divide-slate-100">
          {groups.map(([kind, count]) => (
            <div key={kind} className="flex items-center justify-between py-3">
              <dt className="text-sm text-slate-700">
                {signalLabels[kind] || kind.replaceAll('_', ' ')}
              </dt>
              <dd className="font-mono text-sm font-semibold text-slate-950">
                {count}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  )
}
