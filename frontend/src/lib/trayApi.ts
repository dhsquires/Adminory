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
}
