import axios from 'axios'
import { create } from 'zustand'
import { trayApi } from '@/lib/trayApi'
import { toast } from '@/stores/toastStore'
import {
  EndUser,
  EstateOverview,
  ExecutionTimeseries,
  InstanceFilters,
  Kpi,
  Solution,
  SolutionInstance,
} from '@/types/tray'

interface TrayState {
  workspaceId: string | null
  overview: EstateOverview | null
  solutions: Solution[]
  instances: SolutionInstance[]
  users: EndUser[]
  kpis: Kpi[]
  timeseries: ExecutionTimeseries | null
  selectedInstance: SolutionInstance | null
  filters: InstanceFilters
  isLoading: boolean
  isDetailLoading: boolean
  error: string | null
}

interface TrayActions {
  fetchEstate: (workspaceId: string) => Promise<void>
  fetchInstance: (workspaceId: string, instanceId: string) => Promise<void>
  setFilters: (filters: Partial<InstanceFilters>) => void
  clearFilters: () => void
  clearEstate: () => void
}

type TrayStore = TrayState & TrayActions

const initialEstate = {
  workspaceId: null,
  overview: null,
  solutions: [],
  instances: [],
  users: [],
  kpis: [],
  timeseries: null,
  selectedInstance: null,
  error: null,
}

function errorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<{ detail?: string }>(error)) {
    return error.response?.data?.detail || fallback
  }
  return error instanceof Error ? error.message : fallback
}

export const useTrayStore = create<TrayStore>((set, get) => ({
  ...initialEstate,
  filters: {},
  isLoading: false,
  isDetailLoading: false,

  fetchEstate: async (workspaceId: string) => {
    const workspaceChanged = get().workspaceId !== workspaceId
    set({
      ...(workspaceChanged
        ? {
            overview: null,
            solutions: [],
            instances: [],
            users: [],
            kpis: [],
            timeseries: null,
          }
        : {}),
      isLoading: true,
      isDetailLoading: false,
      error: null,
      workspaceId,
      selectedInstance: null,
    })
    try {
      const [overview, solutions, instances, users, kpis, timeseries] =
        await Promise.all([
          trayApi.overview(workspaceId),
          trayApi.solutions(workspaceId),
          trayApi.instances(workspaceId),
          trayApi.users(workspaceId),
          trayApi.kpis(workspaceId),
          trayApi.timeseries(workspaceId),
        ])

      if (get().workspaceId !== workspaceId) return

      set({
        overview,
        solutions,
        instances,
        users,
        kpis,
        timeseries,
        isLoading: false,
      })
    } catch (error) {
      if (get().workspaceId !== workspaceId) return
      const message = errorMessage(error, 'Failed to load Tray operations data')
      set({ error: message, isLoading: false })
      toast.error('Tray data unavailable', message)
    }
  },

  fetchInstance: async (workspaceId: string, instanceId: string) => {
    set({ isDetailLoading: true, error: null, selectedInstance: null })
    try {
      const instance = await trayApi.instance(workspaceId, instanceId)
      if (get().workspaceId !== workspaceId) return
      set({ selectedInstance: instance, isDetailLoading: false })
    } catch (error) {
      const message = errorMessage(error, 'Failed to load Tray instance')
      set({ error: message, isDetailLoading: false })
      toast.error('Instance unavailable', message)
    }
  },

  setFilters: (filters: Partial<InstanceFilters>) => {
    set((state) => ({ filters: { ...state.filters, ...filters } }))
  },

  clearFilters: () => set({ filters: {} }),

  clearEstate: () =>
    set({
      ...initialEstate,
      filters: {},
      isLoading: false,
      isDetailLoading: false,
    }),
}))
