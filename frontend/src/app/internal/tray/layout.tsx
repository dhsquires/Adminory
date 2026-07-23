'use client'

import { useEffect } from 'react'
import * as Tabs from '@radix-ui/react-tabs'
import { Activity, Boxes, Command, LogOut, Users } from 'lucide-react'
import { usePathname, useRouter } from 'next/navigation'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import WorkspaceSelector from '@/components/workspace/WorkspaceSelector'
import { useAuth } from '@/hooks/useAuth'
import { useTrayStore } from '@/stores/trayStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'

const routes = [
  { value: '/internal/tray', label: 'Command Center', icon: Command },
  { value: '/internal/tray/solutions', label: 'Solutions', icon: Boxes },
  { value: '/internal/tray/instances', label: 'Instances', icon: Activity },
  { value: '/internal/tray/users', label: 'End Users', icon: Users },
] as const

function activeRoute(pathname: string): string {
  return (
    routes.find(
      (route) =>
        route.value !== '/internal/tray' && pathname.startsWith(route.value)
    )?.value || '/internal/tray'
  )
}

export default function TrayLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <ProtectedRoute requireAdmin>
      <TrayShell>{children}</TrayShell>
    </ProtectedRoute>
  )
}

function TrayShell({ children }: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout } = useAuth()
  const currentWorkspace = useWorkspaceStore((state) => state.currentWorkspace)
  const fetchEstate = useTrayStore((state) => state.fetchEstate)
  const clearEstate = useTrayStore((state) => state.clearEstate)

  useEffect(() => {
    if (currentWorkspace?.id) {
      void fetchEstate(currentWorkspace.id)
    } else {
      clearEstate()
    }
  }, [clearEstate, currentWorkspace?.id, fetchEstate])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex min-h-16 max-w-7xl flex-col gap-3 px-4 py-3 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-950">Adminory</p>
              <p className="text-xs text-slate-500">Tray control plane</p>
            </div>
            <WorkspaceSelector />
          </div>
          <div className="flex items-center justify-between gap-4 lg:justify-end">
            <div className="text-right text-xs">
              <p className="font-medium text-slate-700">{user?.name}</p>
              <p className="text-slate-500">{user?.email}</p>
            </div>
            <button
              type="button"
              onClick={() => void logout()}
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              <LogOut aria-hidden="true" className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <Tabs.Root
        value={activeRoute(pathname)}
        onValueChange={(value) => router.push(value)}
      >
        <div className="border-b border-slate-200 bg-white">
          <Tabs.List
            aria-label="Tray operations views"
            className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 sm:px-6 lg:px-8"
          >
            {routes.map((route) => {
              const Icon = route.icon
              return (
                <Tabs.Trigger
                  key={route.value}
                  value={route.value}
                  className="group inline-flex shrink-0 items-center gap-2 border-b-2 border-transparent px-3 py-3 text-sm font-medium text-slate-500 outline-none hover:text-slate-900 focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 data-[state=active]:border-indigo-600 data-[state=active]:text-indigo-700"
                >
                  <Icon aria-hidden="true" className="h-4 w-4" />
                  {route.label}
                </Tabs.Trigger>
              )
            })}
          </Tabs.List>
        </div>
      </Tabs.Root>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}
