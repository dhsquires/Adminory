import Link from 'next/link'
import { ExternalLink } from 'lucide-react'
import { SolutionInstance } from '@/types/tray'
import { HealthBadge } from './HealthBadge'
import { SourceBadge } from './SourceBadge'

interface InstanceTableProps {
  instances: SolutionInstance[]
}

export function InstanceTable({ instances }: InstanceTableProps) {
  if (instances.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
        <h2 className="font-semibold text-slate-900">No instances found</h2>
        <p className="mt-1 text-sm text-slate-500">
          Adjust the filters or choose another workspace.
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-3">
              Instance
            </th>
            <th scope="col" className="px-4 py-3">
              Health
            </th>
            <th scope="col" className="px-4 py-3">
              End user
            </th>
            <th scope="col" className="px-4 py-3">
              Config / auth
            </th>
            <th scope="col" className="px-4 py-3">
              State
            </th>
            <th scope="col" className="px-4 py-3">
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {instances.map((instance) => (
            <tr key={instance.id} className="hover:bg-slate-50">
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div>
                    <p className="font-medium text-slate-900">
                      {instance.name || instance.solution_name || 'Unnamed instance'}
                    </p>
                    <p className="font-mono text-xs text-slate-500">{instance.id}</p>
                  </div>
                  <SourceBadge source={instance.source} />
                </div>
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <HealthBadge status={instance.health?.status || 'warning'} />
              </td>
              <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-600">
                {instance.external_user_id || instance.user_id || '—'}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-600">
                <span>{instance.config_complete ? 'Configured' : 'Missing config'}</span>
                <span aria-hidden="true"> · </span>
                <span>{instance.auth_healthy ? 'Auth healthy' : 'Auth broken'}</span>
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <span className="text-xs font-medium capitalize text-slate-700">
                  {instance.state || (instance.enabled ? 'enabled' : 'disabled')}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right">
                <Link
                  href={`/internal/tray/instances/${encodeURIComponent(
                    instance.id
                  )}`}
                  aria-label={`Open ${instance.name || instance.id}`}
                  className="inline-flex rounded p-1 text-indigo-600 hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <ExternalLink aria-hidden="true" className="h-4 w-4" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
