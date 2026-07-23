'use client'

import { KeyRound, UserRound } from 'lucide-react'
import { HealthBadge } from '@/components/tray/HealthBadge'
import { ProvisionUserDialog } from '@/components/tray/ProvisionUserDialog'
import { SourceBadge } from '@/components/tray/SourceBadge'
import { ProvisionUserInput, trayApi } from '@/lib/trayApi'
import { toast } from '@/stores/toastStore'
import { useTrayStore } from '@/stores/trayStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'

export default function TrayUsersPage() {
  const currentWorkspace = useWorkspaceStore((state) => state.currentWorkspace)
  const { users, isLoading, error, fetchEstate } = useTrayStore()

  if (!currentWorkspace) {
    return <Message title="Choose a workspace" detail="Select a workspace above." />
  }

  if (isLoading && users.length === 0) {
    return <UsersSkeleton />
  }

  if (error && users.length === 0) {
    return <Message title="End users could not load" detail={error} error />
  }

  const provisionUser = async (
    user: ProvisionUserInput,
    confirm: boolean
  ) => {
    const result = await trayApi.provisionUser(
      currentWorkspace.id,
      user,
      confirm
    )
    if (confirm) {
      toast.success('Tray end user provisioned', user.externalUserId)
      await fetchEstate(currentWorkspace.id)
    }
    return result
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-indigo-600">Authentication</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
            End Users
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Token state and authentication health, before everything else.
          </p>
        </div>
        <ProvisionUserDialog onProvision={provisionUser} />
      </div>

      {users.length === 0 ? (
        <Message
          title="No end users found"
          detail="No Tray end users are associated with this workspace."
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th scope="col" className="px-4 py-3">
                  Token status
                </th>
                <th scope="col" className="px-4 py-3">
                  End user
                </th>
                <th scope="col" className="px-4 py-3">
                  Auth health
                </th>
                <th scope="col" className="px-4 py-3">
                  Expires
                </th>
                <th scope="col" className="px-4 py-3">
                  Instances
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((user) => {
                const expired = user.token_status.toLowerCase() === 'expired'
                return (
                  <tr key={user.external_user_id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-semibold ${
                          expired
                            ? 'border-red-200 bg-red-50 text-red-700'
                            : 'border-emerald-200 bg-emerald-50 text-emerald-700'
                        }`}
                      >
                        <KeyRound aria-hidden="true" className="h-3 w-3" />
                        {user.token_status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <UserRound
                          aria-hidden="true"
                          className="h-4 w-4 text-slate-400"
                        />
                        <div>
                          <p className="font-medium text-slate-900">
                            {user.name || user.external_user_id}
                          </p>
                          <p className="font-mono text-xs text-slate-500">
                            {user.user_id || user.external_user_id}
                          </p>
                        </div>
                        <SourceBadge source={user.source} />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <HealthBadge
                        status={
                          expired ? 'critical' : user.auth_healthy ? 'healthy' : 'blocked'
                        }
                      />
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-600">
                      {user.token_expires_at
                        ? new Date(user.token_expires_at).toLocaleString()
                        : 'Unknown'}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-700">
                      {user.instance_count}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
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

function UsersSkeleton() {
  return (
    <div aria-label="Loading end users" className="animate-pulse space-y-5">
      <div className="h-16 w-64 rounded bg-slate-200" />
      <div className="h-80 rounded-lg bg-slate-200" />
    </div>
  )
}
