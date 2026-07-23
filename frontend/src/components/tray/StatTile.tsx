import { ReactNode } from 'react'
import { TraySource } from '@/types/tray'
import { SourceBadge } from './SourceBadge'

interface StatTileProps {
  label: string
  value: string | number
  detail?: string
  icon?: ReactNode
  source?: TraySource
}

export function StatTile({
  label,
  value,
  detail,
  icon,
  source = 'official',
}: StatTileProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              {label}
            </p>
            <SourceBadge source={source} />
          </div>
          <p className="mt-2 font-mono text-2xl font-semibold text-slate-950">
            {value}
          </p>
        </div>
        {icon ? (
          <span className="rounded-md bg-indigo-50 p-2 text-indigo-600">
            {icon}
          </span>
        ) : null}
      </div>
      {detail ? <p className="mt-2 text-xs text-slate-500">{detail}</p> : null}
    </div>
  )
}
