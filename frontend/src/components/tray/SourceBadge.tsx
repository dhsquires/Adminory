import { TraySource } from '@/types/tray'

interface SourceBadgeProps {
  source: TraySource
}

export function SourceBadge({ source }: SourceBadgeProps) {
  if (source !== 'unofficial') return null

  return (
    <span
      className="inline-flex rounded border border-dashed border-slate-300 bg-slate-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500"
      title="Reverse-engineered endpoint; verify in Tray UI"
    >
      unofficial
    </span>
  )
}
