import { apiClient } from '@/lib/api'
import {
  EndUser,
  EstateOverview,
  ExecutionTimeseries,
  InstanceFilters,
  Kpi,
  Solution,
  SolutionInstance,
} from '@/types/tray'

const TRAY_API = '/api/internal/tray'

function workspaceConfig(workspaceId: string, params?: Record<string, string>) {
  return {
    params: {
      workspace_id: workspaceId,
      ...params,
    },
  }
}

export const trayApi = {
  overview(workspaceId: string): Promise<EstateOverview> {
    return apiClient.get<EstateOverview>(
      `${TRAY_API}/overview`,
      workspaceConfig(workspaceId)
    )
  },

  solutions(workspaceId: string): Promise<Solution[]> {
    return apiClient.get<Solution[]>(
      `${TRAY_API}/solutions`,
      workspaceConfig(workspaceId)
    )
  },

  instances(
    workspaceId: string,
    filters: InstanceFilters = {}
  ): Promise<SolutionInstance[]> {
    const params = Object.fromEntries(
      Object.entries(filters).filter((entry): entry is [string, string] =>
        Boolean(entry[1])
      )
    )
    return apiClient.get<SolutionInstance[]>(
      `${TRAY_API}/instances`,
      workspaceConfig(workspaceId, params)
    )
  },

  instance(workspaceId: string, instanceId: string): Promise<SolutionInstance> {
    return apiClient.get<SolutionInstance>(
      `${TRAY_API}/instances/${encodeURIComponent(instanceId)}`,
      workspaceConfig(workspaceId)
    )
  },

  users(workspaceId: string): Promise<EndUser[]> {
    return apiClient.get<EndUser[]>(
      `${TRAY_API}/users`,
      workspaceConfig(workspaceId)
    )
  },

  kpis(workspaceId: string): Promise<Kpi[]> {
    return apiClient.get<Kpi[]>(
      `${TRAY_API}/insights/kpis`,
      workspaceConfig(workspaceId)
    )
  },

  timeseries(workspaceId: string): Promise<ExecutionTimeseries> {
    return apiClient.get<ExecutionTimeseries>(
      `${TRAY_API}/insights/timeseries`,
      workspaceConfig(workspaceId)
    )
  },

  enableInstance(
    workspaceId: string,
    instanceId: string,
    confirm = false
  ): Promise<MutationResult> {
    return apiClient.post<MutationResult>(
      `${TRAY_API}/instances/${encodeURIComponent(instanceId)}/enable`,
      undefined,
      mutationConfig(workspaceId, confirm)
    )
  },

  disableInstance(
    workspaceId: string,
    instanceId: string,
    confirm = false
  ): Promise<MutationResult> {
    return apiClient.post<MutationResult>(
      `${TRAY_API}/instances/${encodeURIComponent(instanceId)}/disable`,
      undefined,
      mutationConfig(workspaceId, confirm)
    )
  },

  deleteInstance(
    workspaceId: string,
    instanceId: string,
    confirm = false
  ): Promise<MutationResult> {
    return apiClient.delete<MutationResult>(
      `${TRAY_API}/instances/${encodeURIComponent(instanceId)}`,
      mutationConfig(workspaceId, confirm)
    )
  },

  updateInstanceConfig(
    workspaceId: string,
    instanceId: string,
    update: InstanceConfigUpdate,
    confirm = false
  ): Promise<MutationResult> {
    return apiClient.post<MutationResult>(
      `${TRAY_API}/instances/${encodeURIComponent(instanceId)}/config`,
      update,
      mutationConfig(workspaceId, confirm)
    )
  },

  provisionUser(
    workspaceId: string,
    user: ProvisionUserInput,
    confirm = false
  ): Promise<MutationResult> {
    return apiClient.post<MutationResult>(
      `${TRAY_API}/users`,
      user,
      mutationConfig(workspaceId, confirm)
    )
  },

  reauthorizeUser(
    workspaceId: string,
    userId: string,
    confirm = false
  ): Promise<MutationResult> {
    return apiClient.post<MutationResult>(
      `${TRAY_API}/users/${encodeURIComponent(userId)}/reauthorize`,
      undefined,
      mutationConfig(workspaceId, confirm)
    )
  },

  wizardUrl(
    workspaceId: string,
    userId: string,
    identifiers: WizardUrlInput,
    confirm = false
  ): Promise<MutationResult> {
    return apiClient.post<MutationResult>(
      `${TRAY_API}/users/${encodeURIComponent(userId)}/wizard-url`,
      identifiers,
      mutationConfig(workspaceId, confirm)
    )
  },

  publishSolution(
    workspaceId: string,
    solutionId: string,
    confirm = false
  ): Promise<MutationResult> {
    return apiClient.post<MutationResult>(
      `${TRAY_API}/solutions/${encodeURIComponent(solutionId)}/publish`,
      undefined,
      mutationConfig(workspaceId, confirm)
    )
  },
}

function mutationConfig(workspaceId: string, confirm: boolean) {
  return workspaceConfig(workspaceId, {
    confirm: String(confirm),
  })
}

export interface ConfigValueInput {
  externalId: string
  value: unknown
}

export interface AuthValueInput {
  externalId: string
  authId: string
}

export interface InstanceConfigUpdate {
  config_values: ConfigValueInput[]
  auth_values: AuthValueInput[]
  enable?: boolean
}

export interface MutationResult {
  dry_run: boolean
  would_send: Record<string, unknown>
  applied: boolean
  warning?: string | null
}

export interface ProvisionUserInput {
  name: string
  externalUserId: string
}

export interface WizardUrlInput {
  solution_id: string
  instance_id: string
}
