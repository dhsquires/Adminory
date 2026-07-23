'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Pause, RefreshCw, RotateCcw, Workflow } from 'lucide-react'
import { useParams } from 'next/navigation'
import { ExecutionsChart } from '@/components/tray/ExecutionsChart'
import { HealthBadge } from '@/components/tray/HealthBadge'
import { SlotStatusTable } from '@/components/tray/SlotStatusTable'
import { SourceBadge } from '@/components/tray/SourceBadge'
import { useTrayStore } from '@/stores/trayStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import { TimeseriesPoint, TrayWorkflow } from '@/types/tray'

export default function TrayInstanceDetailPage() {
  const params = useParams<{ id: string }>()
  const instanceId = params.id
  const currentWorkspace = useWorkspaceStore((state) => state.currentWorkspace)
  const {
    selectedInstance,
    timeseries,
    isLoading,
    isDetailLoading,
    error,
    fetchInstance,
  } = useTrayStore()

  useEffect(() => {
    if (
      currentWorkspace?.id &&
      !isLoading &&
      !isDetailLoading &&
      selectedInstance?.id !== instanceId
    ) {
      void fetchInstance(currentWorkspace.id, instanceId)
    }
  }, [
    currentWorkspace?.id,
    fetchInstance,
    instanceId,
    isDetailLoading,
    isLoading,
    selectedInstance?.id,
  ])

  if (!currentWorkspace) {
    return <Message title="Choose a workspace" detail="Select a workspace above." />
  }

  if ((isLoading || isDetailLoading) && selectedInstance?.id !== instanceId) {
    return <DetailSkeleton />
  }

  if (error && selectedInstance?.id !== instanceId) {
    return <Message title="Instance could not load" detail={error} error />
  }

  if (!selectedInstance || selectedInstance.id !== instanceId) return null

  const instance = selectedInstance
  const hasRecentExecutions = instance.recent_executions.length > 0
  const executionData: TimeseriesPoint[] = hasRecentExecutions
    ? instance.recent_executions
    : timeseries?.data || []
  const executionSource = hasRecentExecutions
    ? instance.source
    : timeseries?.source || instance.source

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/internal/tray/instances"
          className="inline-flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          All instances
        </Link>
        <div className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <HealthBadge status={instance.health?.status || 'warning'} />
              <SourceBadge source={instance.source} />
            </div>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
              {instance.name || instance.solution_name || 'Unnamed instance'}
            </h1>
            <p className="mt-1 font-mono text-xs text-slate-500">{instance.id}</p>
          </div>
          <div
            aria-label="Instance actions unavailable"
            className="flex flex-wrap gap-2"
          >
            <DisabledAction icon={RefreshCw} label="Refresh auth" />
            <DisabledAction icon={RotateCcw} label="Restart" />
            <DisabledAction icon={Pause} label="Disable" />
          </div>
        </div>
        <p className="mt-3 text-xs font-medium text-slate-500">
          Actions are visible for operator context and will be wired in track 04.
        </p>
      </div>

      <section
        aria-labelledby="instance-summary-heading"
        className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
      >
        <h2
          id="instance-summary-heading"
          className="text-lg font-semibold text-slate-950"
        >
          Instance summary
        </h2>
        <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <SummaryItem label="Solution" value={instance.solution_name || instance.solution_id || '—'} />
          <SummaryItem
            label="End user"
            value={instance.external_user_id || instance.user_id || '—'}
            mono
          />
          <SummaryItem
            label="State"
            value={instance.state || (instance.enabled ? 'Enabled' : 'Disabled')}
          />
          <SummaryItem label="Version" value={instance.version || '—'} mono />
          <SummaryItem
            label="Configuration"
            value={instance.config_complete ? 'Complete' : 'Missing required values'}
          />
          <SummaryItem
            label="Authentication"
            value={instance.auth_healthy ? 'Healthy' : 'Broken'}
          />
          <SummaryItem
            label="Token"
            value={instance.token_status || (instance.token_expired ? 'Expired' : 'Unknown')}
          />
          <SummaryItem
            label="Created"
            value={
              instance.created_at
                ? new Date(instance.created_at).toLocaleString()
                : 'Unknown'
            }
          />
        </dl>
        {instance.missing_required_config.length > 0 ? (
          <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3">
            <p className="text-sm font-semibold text-amber-900">
              Missing required configuration
            </p>
            <p className="mt-1 font-mono text-xs text-amber-800">
              {instance.missing_required_config.join(', ')}
            </p>
          </div>
        ) : null}
      </section>

      <WorkflowsTable workflows={instance.workflows} />

      <div className="grid gap-6 xl:grid-cols-2">
        <SlotStatusTable title="Configuration slots" slots={instance.config_slots} />
        <SlotStatusTable title="Authentication slots" slots={instance.auth_slots} />
      </div>

      <ExecutionsChart
        data={executionData}
        source={executionSource}
      />
    </div>
  )
}

function DisabledAction({
  icon: Icon,
  label,
}: {
  icon: typeof RefreshCw
  label: string
}) {
  return (
    <button
      type="button"
      disabled
      title={`${label} will be wired in track 04`}
      className="inline-flex cursor-not-allowed items-center gap-2 rounded-md border border-slate-200 bg-slate-100 px-3 py-2 text-sm font-medium text-slate-400"
    >
      <Icon aria-hidden="true" className="h-4 w-4" />
      {label}
    </button>
  )
}

function SummaryItem({
  label,
  value,
  mono = false,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd className={`mt-1 text-slate-900 ${mono ? 'font-mono text-xs' : ''}`}>
        {value}
      </dd>
    </div>
  )
}

function workflowName(workflow: TrayWorkflow, index: number): string {
  return String(workflow.name || workflow.title || workflow.id || `Workflow ${index + 1}`)
}

function WorkflowsTable({ workflows }: { workflows: TrayWorkflow[] }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
        <Workflow aria-hidden="true" className="h-5 w-5 text-indigo-600" />
        <h2 className="text-lg font-semibold text-slate-950">Workflows</h2>
      </div>
      {workflows.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-slate-500">
          No workflows reported for this instance.
        </p>
      ) : (
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="px-4 py-3">
                Workflow
              </th>
              <th scope="col" className="px-4 py-3">
                State
              </th>
              <th scope="col" className="px-4 py-3">
                Enabled
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {workflows.map((workflow, index) => (
              <tr key={String(workflow.id || workflowName(workflow, index))}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {workflowName(workflow, index)}
                </td>
                <td className="px-4 py-3 capitalize text-slate-600">
                  {String(workflow.state || workflow.status || 'Unknown')}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {typeof workflow.enabled === 'boolean'
                    ? workflow.enabled
                      ? 'Enabled'
                      : 'Disabled'
                    : 'Unknown'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
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

function DetailSkeleton() {
  return (
    <div aria-label="Loading instance detail" className="animate-pulse space-y-6">
      <div className="h-24 w-96 max-w-full rounded bg-slate-200" />
      <div className="h-48 rounded-lg bg-slate-200" />
      <div className="h-64 rounded-lg bg-slate-200" />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-52 rounded-lg bg-slate-200" />
        <div className="h-52 rounded-lg bg-slate-200" />
      </div>
    </div>
  )
}
