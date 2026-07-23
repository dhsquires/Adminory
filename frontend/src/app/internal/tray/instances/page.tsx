'use client'

import { useMemo } from 'react'
import { FilterX, Search } from 'lucide-react'
import { InstanceTable } from '@/components/tray/InstanceTable'
import { useTrayStore } from '@/stores/trayStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import { SolutionInstance } from '@/types/tray'

function matchesFilters(
  instance: SolutionInstance,
  filters: ReturnType<typeof useTrayStore.getState>['filters']
) {
  if (filters.state && instance.health?.status !== filters.state) return false
  if (filters.config === 'complete' && !instance.config_complete) return false
  if (filters.config === 'missing' && instance.config_complete) return false
  if (filters.auth === 'healthy' && !instance.auth_healthy) return false
  if (filters.auth === 'broken' && !instance.auth_broken) return false
  if (filters.auth === 'expired' && !instance.token_expired) return false

  const search = filters.solution?.trim().toLowerCase()
  if (search) {
    const haystack = [
      instance.id,
      instance.name,
      instance.solution_id,
      instance.solution_name,
      instance.user_id,
      instance.external_user_id,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    if (!haystack.includes(search)) return false
  }

  return true
}

export default function TrayInstancesPage() {
  const currentWorkspace = useWorkspaceStore((state) => state.currentWorkspace)
  const {
    instances,
    filters,
    setFilters,
    clearFilters,
    isLoading,
    error,
  } = useTrayStore()
  const filteredInstances = useMemo(
    () => instances.filter((instance) => matchesFilters(instance, filters)),
    [filters, instances]
  )

  if (!currentWorkspace) {
    return <Message title="Choose a workspace" detail="Select a workspace above." />
  }

  if (isLoading && instances.length === 0) {
    return <InstancesSkeleton />
  }

  if (error && instances.length === 0) {
    return <Message title="Instances could not load" detail={error} error />
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-indigo-600">Estate</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
          Instances
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Health-scored installations across {currentWorkspace.name}.
        </p>
      </div>

      <section
        aria-label="Instance filters"
        className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      >
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-5">
          <label className="relative lg:col-span-2">
            <span className="sr-only">Search instances</span>
            <Search
              aria-hidden="true"
              className="absolute left-3 top-2.5 h-4 w-4 text-slate-400"
            />
            <input
              value={filters.solution || ''}
              onChange={(event) => setFilters({ solution: event.target.value })}
              placeholder="Search solution, user, or ID"
              className="w-full rounded-md border border-slate-300 py-2 pl-9 pr-3 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
            />
          </label>
          <label>
            <span className="sr-only">Health status</span>
            <select
              value={filters.state || ''}
              onChange={(event) => setFilters({ state: event.target.value })}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
            >
              <option value="">All health</option>
              <option value="healthy">Healthy</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
              <option value="blocked">Blocked</option>
              <option value="dead_install">Dead install</option>
            </select>
          </label>
          <label>
            <span className="sr-only">Configuration status</span>
            <select
              value={filters.config || ''}
              onChange={(event) => setFilters({ config: event.target.value })}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
            >
              <option value="">All config</option>
              <option value="complete">Configured</option>
              <option value="missing">Missing config</option>
            </select>
          </label>
          <label>
            <span className="sr-only">Authentication status</span>
            <select
              value={filters.auth || ''}
              onChange={(event) => setFilters({ auth: event.target.value })}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
            >
              <option value="">All auth</option>
              <option value="healthy">Healthy</option>
              <option value="broken">Broken</option>
              <option value="expired">Expired</option>
            </select>
          </label>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing {filteredInstances.length} of {instances.length}
          </span>
          <button
            type="button"
            onClick={clearFilters}
            className="inline-flex items-center gap-1 rounded px-2 py-1 font-semibold text-slate-600 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <FilterX aria-hidden="true" className="h-4 w-4" />
            Clear filters
          </button>
        </div>
      </section>

      <InstanceTable instances={filteredInstances} />
    </div>
  )
}

function Message({
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

function InstancesSkeleton() {
  return (
    <div aria-label="Loading instances" className="animate-pulse space-y-5">
      <div className="h-16 w-64 rounded bg-slate-200" />
      <div className="h-24 rounded-lg bg-slate-200" />
      <div className="h-80 rounded-lg bg-slate-200" />
    </div>
  )
}
