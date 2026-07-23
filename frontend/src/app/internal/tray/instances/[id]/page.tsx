'use client'

import { useEffect, useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import Link from 'next/link'
import {
  ArrowLeft,
  Pause,
  PlayCircle,
  RefreshCw,
  RotateCcw,
  Trash2,
  Workflow,
  X,
} from 'lucide-react'
import { useParams, useRouter } from 'next/navigation'
import { ConfigEditor } from '@/components/tray/ConfigEditor'
import { ExecutionsChart } from '@/components/tray/ExecutionsChart'
import { HealthBadge } from '@/components/tray/HealthBadge'
import { SlotStatusTable } from '@/components/tray/SlotStatusTable'
import { SourceBadge } from '@/components/tray/SourceBadge'
import { MutationResult, trayApi } from '@/lib/trayApi'
import { toast } from '@/stores/toastStore'
import { useTrayStore } from '@/stores/trayStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import { TimeseriesPoint, TrayWorkflow } from '@/types/tray'

type InstanceAction = 'enable' | 'disable' | 'reauthorize' | 'wizard'

export default function TrayInstanceDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
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
  const [actionPreview, setActionPreview] = useState<{
    action: InstanceAction
    result: MutationResult
  } | null>(null)
  const [isMutating, setIsMutating] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

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
  const canManageUser = Boolean(instance.user_id)
  const canRunWizard = Boolean(
    instance.user_id && instance.solution_id && instance.id
  )

  const runAction = async (action: InstanceAction, confirm: boolean) => {
    setIsMutating(true)
    setActionError(null)
    try {
      let result: MutationResult
      if (action === 'enable') {
        result = await trayApi.enableInstance(
          currentWorkspace.id,
          instance.id,
          confirm
        )
      } else if (action === 'disable') {
        result = await trayApi.disableInstance(
          currentWorkspace.id,
          instance.id,
          confirm
        )
      } else if (action === 'reauthorize') {
        if (!instance.user_id) throw new Error('This instance has no Tray user ID')
        result = await trayApi.reauthorizeUser(
          currentWorkspace.id,
          instance.user_id,
          confirm
        )
      } else {
        if (!instance.user_id || !instance.solution_id) {
          throw new Error('This instance is missing its Tray user or Solution ID')
        }
        result = await trayApi.wizardUrl(
          currentWorkspace.id,
          instance.user_id,
          {
            solution_id: instance.solution_id,
            instance_id: instance.id,
          },
          confirm
        )
      }

      if (!confirm) {
        setActionPreview({ action, result })
      } else {
        const wizardResult = result.would_send.result
        const wizardUrl =
          typeof wizardResult === 'object' &&
          wizardResult !== null &&
          'wizard_url' in wizardResult &&
          typeof wizardResult.wizard_url === 'string'
            ? wizardResult.wizard_url
            : null
        if (action === 'wizard' && wizardUrl) {
          window.open(wizardUrl, '_blank', 'noopener,noreferrer')
        }
        toast.success('Tray mutation applied', actionLabel(action))
        setActionPreview(null)
        await fetchInstance(currentWorkspace.id, instance.id)
      }
      return result
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : 'Tray mutation failed'
      setActionError(message)
      toast.error('Tray mutation failed', message)
    } finally {
      setIsMutating(false)
    }
  }

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
          <div aria-label="Instance actions" className="flex flex-wrap gap-2">
            <ActionButton
              icon={RefreshCw}
              label="Re-authorize"
              disabled={!canManageUser || isMutating}
              onClick={() => void runAction('reauthorize', false)}
            />
            <ActionButton
              icon={RotateCcw}
              label="Re-run Config Wizard"
              disabled={!canRunWizard || isMutating}
              onClick={() => void runAction('wizard', false)}
            />
            {instance.enabled ? (
              <ActionButton
                icon={Pause}
                label="Disable"
                disabled={isMutating}
                onClick={() => void runAction('disable', false)}
              />
            ) : (
              <ActionButton
                icon={PlayCircle}
                label="Enable"
                disabled={isMutating}
                onClick={() => void runAction('enable', false)}
              />
            )}
            <DisabledAction
              icon={RefreshCw}
              label="Upgrade"
              title="Upgrade wire name is unconfirmed"
            />
            <DeleteInstanceDialog
              instanceId={instance.id}
              workspaceId={currentWorkspace.id}
              disabled={isMutating}
              onDeleted={async () => {
                router.push('/internal/tray/instances')
              }}
            />
          </div>
        </div>
        <p className="mt-3 text-xs font-medium text-slate-500">
          Every action previews its exact dry-run payload before live confirmation.
        </p>
        {actionError ? (
          <p role="alert" className="mt-2 text-sm text-red-700">
            {actionError}
          </p>
        ) : null}
        {actionPreview ? (
          <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4">
            <p className="text-sm font-semibold text-amber-950">
              Dry run: {actionLabel(actionPreview.action)}
            </p>
            <p className="mt-1 text-sm text-amber-900">Will send</p>
            <pre className="mt-2 max-h-64 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">
              {JSON.stringify(actionPreview.result.would_send, null, 2)}
            </pre>
            <button
              type="button"
              disabled={isMutating}
              onClick={() =>
                void runAction(actionPreview.action, true).catch(() => undefined)
              }
              className="mt-3 rounded-md bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-50"
            >
              Confirm live {actionLabel(actionPreview.action).toLowerCase()}
            </button>
          </div>
        ) : null}
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

      <ConfigEditor
        configSlots={instance.config_slots}
        authSlots={instance.auth_slots}
        onDryRun={(update) =>
          trayApi.updateInstanceConfig(
            currentWorkspace.id,
            instance.id,
            update,
            false
          )
        }
        onApply={async (update) => {
          await trayApi.updateInstanceConfig(
            currentWorkspace.id,
            instance.id,
            update,
            true
          )
          toast.success('Instance configuration applied', instance.id)
          await fetchInstance(currentWorkspace.id, instance.id)
        }}
        onReconnect={() => void runAction('wizard', false)}
      />

      <ExecutionsChart
        data={executionData}
        source={executionSource}
      />
    </div>
  )
}

function actionLabel(action: InstanceAction): string {
  const labels: Record<InstanceAction, string> = {
    enable: 'Enable',
    disable: 'Disable',
    reauthorize: 'Re-authorize',
    wizard: 'Re-run Config Wizard',
  }
  return labels[action]
}

function ActionButton({
  icon: Icon,
  label,
  disabled,
  onClick,
}: {
  icon: typeof RefreshCw
  label: string
  disabled: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
    >
      <Icon aria-hidden="true" className="h-4 w-4" />
      {label}
    </button>
  )
}

function DisabledAction({
  icon: Icon,
  label,
  title,
}: {
  icon: typeof RefreshCw
  label: string
  title: string
}) {
  return (
    <button
      type="button"
      disabled
      title={title}
      className="inline-flex cursor-not-allowed items-center gap-2 rounded-md border border-slate-200 bg-slate-100 px-3 py-2 text-sm font-medium text-slate-400"
    >
      <Icon aria-hidden="true" className="h-4 w-4" />
      {label}
    </button>
  )
}

function DeleteInstanceDialog({
  instanceId,
  workspaceId,
  disabled,
  onDeleted,
}: {
  instanceId: string
  workspaceId: string
  disabled: boolean
  onDeleted: () => Promise<void>
}) {
  const [open, setOpen] = useState(false)
  const [preview, setPreview] = useState<MutationResult | null>(null)
  const [isWorking, setIsWorking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const previewDelete = async () => {
    setIsWorking(true)
    setError(null)
    try {
      setPreview(await trayApi.deleteInstance(workspaceId, instanceId, false))
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : 'Could not prepare dry run'
      )
    } finally {
      setIsWorking(false)
    }
  }

  const applyDelete = async () => {
    setIsWorking(true)
    setError(null)
    try {
      await trayApi.deleteInstance(workspaceId, instanceId, true)
      toast.success('Tray instance deleted', instanceId)
      setOpen(false)
      await onDeleted()
    } catch (caught) {
      const message =
        caught instanceof Error ? caught.message : 'Could not delete instance'
      setError(message)
      toast.error('Tray deletion failed', message)
    } finally {
      setIsWorking(false)
    }
  }

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen)
        if (!nextOpen) {
          setPreview(null)
          setError(null)
        }
      }}
    >
      <Dialog.Trigger asChild>
        <button
          type="button"
          disabled={disabled}
          className="inline-flex items-center gap-2 rounded-md border border-red-300 bg-white px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
        >
          <Trash2 aria-hidden="true" className="h-4 w-4" />
          Delete
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-slate-950/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[90vh] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-auto rounded-lg bg-white p-6 shadow-xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="text-lg font-semibold text-red-900">
                Delete live Tray instance?
              </Dialog.Title>
              <Dialog.Description className="mt-2 text-sm text-slate-700">
                Deleting this instance halts its workflows mid-execution and
                cannot be undone.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Close"
                className="rounded p-1 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <X aria-hidden="true" className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>

          <p className="mt-3 font-mono text-xs text-slate-500">{instanceId}</p>
          {error ? (
            <p role="alert" className="mt-3 text-sm text-red-700">
              {error}
            </p>
          ) : null}
          {!preview ? (
            <button
              type="button"
              disabled={isWorking}
              onClick={() => void previewDelete()}
              className="mt-5 rounded-md bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-900 disabled:opacity-50"
            >
              Review deletion dry run
            </button>
          ) : (
            <div className="mt-5 rounded-md border border-red-200 bg-red-50 p-4">
              <p className="text-sm font-semibold text-red-900">Will send</p>
              <pre className="mt-2 max-h-48 overflow-auto rounded bg-slate-950 p-3 text-xs text-white">
                {JSON.stringify(preview.would_send, null, 2)}
              </pre>
              <button
                type="button"
                disabled={isWorking}
                onClick={() => void applyDelete()}
                className="mt-3 rounded-md bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-50"
              >
                Confirm permanent deletion
              </button>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
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
