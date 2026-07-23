'use client'

import { AlertTriangle, Box } from 'lucide-react'
import { LifecycleFlow } from '@/components/tray/LifecycleFlow'
import { SourceBadge } from '@/components/tray/SourceBadge'
import { useTrayStore } from '@/stores/trayStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'

export default function TraySolutionsPage() {
  const currentWorkspace = useWorkspaceStore((state) => state.currentWorkspace)
  const { solutions, isLoading, error } = useTrayStore()

  if (!currentWorkspace) {
    return <PageMessage title="Choose a workspace" detail="Select a workspace above." />
  }

  if (isLoading && solutions.length === 0) {
    return <TableSkeleton />
  }

  if (error && solutions.length === 0) {
    return <PageMessage title="Solutions could not load" detail={error} error />
  }

  const drifted = solutions.filter((solution) => solution.drift).length

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-indigo-600">Registry</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
            Solutions
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Published versions and active estate coverage.
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <AlertTriangle aria-hidden="true" className="h-4 w-4 text-amber-500" />
          {drifted} with version drift
        </div>
      </div>

      <LifecycleFlow solutions={solutions} />

      {solutions.length === 0 ? (
        <PageMessage
          title="No solutions found"
          detail="This workspace has no Tray solutions."
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th scope="col" className="px-4 py-3">
                  Solution
                </th>
                <th scope="col" className="px-4 py-3">
                  State
                </th>
                <th scope="col" className="px-4 py-3">
                  Current
                </th>
                <th scope="col" className="px-4 py-3">
                  Latest
                </th>
                <th scope="col" className="px-4 py-3">
                  Active instances
                </th>
                <th scope="col" className="px-4 py-3">
                  Drift
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {solutions.map((solution) => (
                <tr key={solution.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Box aria-hidden="true" className="h-4 w-4 text-slate-400" />
                      <div>
                        <p className="font-medium text-slate-900">
                          {solution.name || 'Unnamed solution'}
                        </p>
                        <p className="font-mono text-xs text-slate-500">
                          {solution.id}
                        </p>
                      </div>
                      <SourceBadge source={solution.source} />
                    </div>
                  </td>
                  <td className="px-4 py-3 capitalize text-slate-700">
                    {solution.state || 'Unknown'}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">
                    {solution.version || '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">
                    {solution.latest_version || '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-700">
                    {solution.active_instances}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-semibold ${
                        solution.drift ? 'text-amber-700' : 'text-emerald-700'
                      }`}
                    >
                      {solution.drift ? 'Drift detected' : 'Current'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function PageMessage({
  title,
  detail,
  error = false,
}: {
  title: string
  detail: string
  error?: boolean
}) {
  return (
    <div
      role={error ? 'alert' : undefined}
      className={`rounded-lg border px-6 py-12 text-center ${
        error
          ? 'border-red-200 bg-red-50 text-red-800'
          : 'border-dashed border-slate-300 bg-white text-slate-600'
      }`}
    >
      <h1 className="font-semibold">{title}</h1>
      <p className="mt-1 text-sm">{detail}</p>
    </div>
  )
}

function TableSkeleton() {
  return (
    <div aria-label="Loading solutions" className="animate-pulse space-y-5">
      <div className="h-16 w-64 rounded bg-slate-200" />
      <div className="h-32 rounded-lg bg-slate-200" />
      <div className="h-72 rounded-lg bg-slate-200" />
    </div>
  )
}
