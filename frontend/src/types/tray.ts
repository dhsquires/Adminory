export type TraySource = 'official' | 'unofficial'

export type HealthStatus =
  | 'healthy'
  | 'warning'
  | 'critical'
  | 'blocked'
  | 'dead_install'

export type SignalKind =
  | 'expired_token'
  | 'misconfigured'
  | 'version_drift'
  | 'error_spike'
  | 'dead_install'
  | 'auth_broken'

export interface HealthScore {
  instance_id: string | null
  status: HealthStatus
  reasons: string[]
  source: TraySource
}

export interface Solution {
  id: string
  name: string
  state: string | null
  version: string | null
  latest_version: string | null
  active_instances: number
  drift: boolean
  source: TraySource
}

export interface TrayWorkflow {
  id?: string
  name?: string
  title?: string
  state?: string
  status?: string
  enabled?: boolean
  [key: string]: unknown
}

export interface TraySlot {
  id?: string
  key?: string
  name?: string
  title?: string
  label?: string
  status?: string
  configured?: boolean
  required?: boolean
  [key: string]: unknown
}

export interface TrayExecution {
  id?: string
  time?: string
  date?: string
  timestamp?: string
  created_at?: string
  value?: number
  count?: number
  executions?: number
  status?: string
  [key: string]: unknown
}

export interface SolutionInstance {
  id: string
  name: string
  solution_id: string | null
  solution_name: string | null
  user_id: string | null
  external_user_id: string | null
  enabled: boolean
  ever_enabled: boolean
  state: string | null
  version: string | null
  config_complete: boolean
  missing_required_config: string[]
  auth_healthy: boolean
  auth_broken: boolean
  token_expired: boolean
  token_status: string | null
  created_at: string | null
  workflows: TrayWorkflow[]
  config_slots: TraySlot[]
  auth_slots: TraySlot[]
  recent_executions: TrayExecution[]
  health: HealthScore | null
  source: TraySource
}

export interface EndUser {
  external_user_id: string
  user_id: string | null
  name: string | null
  token_status: string
  token_expires_at: string | null
  instance_count: number
  auth_healthy: boolean
  source: TraySource
}

export interface Kpi {
  instance_id: string | null
  executions: number
  successful: number
  failed: number
  success_rate: number
  error_rate: number
  source: TraySource
}

export interface TriageSignal {
  kind: SignalKind
  instance_id: string
  solution_id: string | null
  user_id: string | null
  title: string
  reason: string
  severity: HealthStatus
  users_at_risk: number
  executions_at_risk: number
  blast_radius: number
  source: TraySource
}

export interface EstateOverview {
  total_solutions: number
  total_instances: number
  enabled_instances: number
  enabled_ratio: number
  total_users: number
  total_executions: number
  success_rate: number
  healthy_instances: number
  warning_instances: number
  critical_instances: number
  blocked_instances: number
  dead_install_instances: number
  triage: TriageSignal[]
  signal_counts: Record<string, number>
  source: TraySource
}

export interface TimeseriesPoint {
  time?: string
  date?: string
  timestamp?: string
  value?: number
  count?: number
  executions?: number
  [key: string]: unknown
}

export interface ExecutionTimeseries {
  data: TimeseriesPoint[]
  source: TraySource
  [key: string]: unknown
}

export interface InstanceFilters {
  state?: string
  config?: string
  auth?: string
  error?: string
  solution?: string
  user?: string
}
