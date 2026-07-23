'use client'

import { Activity, Boxes, Users, Workflow } from 'lucide-react'
import { SignalGroups } from '@/components/tray/SignalGroups'
import { StatTile } from '@/components/tray/StatTile'
import { TriageQueue } from '@/components/tray/TriageQueue'
import { useTrayStore } from '@/stores/trayStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'

export default function TrayCommandCenterPage() {
  const currentWorkspace = useWorkspaceStore((state) => state.currentWorkspace)
  const { overview, isLoading, error } = useTrayStore()

  if (!currentWorkspace) {
    return <WorkspaceEmptyState />
  }

  if (isLoading && !overview) {
    return <CommandCenterSkeleton />
  }

  if (error && !overview) {
    return <ErrorState message={error} />
  }

  if (!overview) return null

  const enabledPercent = Math.round(overview.enabled_ratio * 100)
  const successPercent = Math.round(overview.success_rate * 1000) / 10

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-indigo-600">Operations</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
          Command Center
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          What needs attention across {currentWorkspace.name}.
        </p>
      </div>

      <TriageQueue signals={overview.triage} />

      <section aria-labelledby="estate-heading">
        <h2 id="estate-heading" className="sr-only">
          Estate summary
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile
            label="Solutions"
            value={overview.total_solutions}
            detail={`${overview.total_instances} total instances`}
            icon={<Boxes aria-hidden="true" className="h-5 w-5" />}
            source={overview.source}
          />
          <StatTile
            label="Enabled"
            value={`${enabledPercent}%`}
            detail={`${overview.enabled_instances} enabled instances`}
            icon={<Activity aria-hidden="true" className="h-5 w-5" />}
            source={overview.source}
          />
          <StatTile
            label="End users"
            value={overview.total_users}
            detail={`${overview.healthy_instances} healthy instances collapsed`}
            icon={<Users aria-hidden="true" className="h-5 w-5" />}
            source={overview.source}
          />
          <StatTile
            label="Success rate"
            value={`${successPercent}%`}
            detail={`${overview.total_executions.toLocaleString()} executions`}
            icon={<Workflow aria-hidden="true" className="h-5 w-5" />}
            source={overview.source}
          />
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-5 py-4">
          <p className="text-sm font-semibold text-emerald-800">
            Healthy estate summarized
          </p>
          <p className="mt-1 text-sm text-emerald-700">
            {overview.healthy_instances} healthy instances are collapsed to keep
            operator focus on actionable work.
          </p>
        </div>
        <SignalGroups
          counts={overview.signal_counts}
          source={overview.source}
        />
      </div>
    </div>
  )
}

function WorkspaceEmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
      <h1 className="text-xl font-semibold text-slate-900">Choose a workspace</h1>
      <p className="mt-2 text-sm text-slate-500">
        Select a workspace above to load its Tray estate.
      </p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-5">
      <h1 className="font-semibold text-red-900">Tray estate could not load</h1>
      <p className="mt-1 text-sm text-red-700">{message}</p>
    </div>
  )
}

function CommandCenterSkeleton() {
  return (
    <div aria-label="Loading command center" className="animate-pulse space-y-6">
      <div className="h-16 w-72 rounded bg-slate-200" />
      <div className="h-72 rounded-lg bg-slate-200" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <div key={item} className="h-28 rounded-lg bg-slate-200" />
        ))}
      </div>
    </div>
  )
}
