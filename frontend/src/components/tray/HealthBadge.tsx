import {
  AlertOctagon,
  AlertTriangle,
  Ban,
  CheckCircle2,
  CircleOff,
} from 'lucide-react'
import { HealthStatus } from '@/types/tray'

const healthStyles = {
  healthy: {
    label: 'Healthy',
    className: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    icon: CheckCircle2,
  },
  warning: {
    label: 'Warning',
    className: 'border-amber-200 bg-amber-50 text-amber-700',
    icon: AlertTriangle,
  },
  critical: {
    label: 'Critical',
    className: 'border-red-200 bg-red-50 text-red-700',
    icon: AlertOctagon,
  },
  blocked: {
    label: 'Blocked',
    className: 'border-violet-200 bg-violet-50 text-violet-700',
    icon: Ban,
  },
  dead_install: {
    label: 'Dead install',
    className: 'border-gray-300 bg-gray-100 text-gray-700',
    icon: CircleOff,
  },
} as const

interface HealthBadgeProps {
  status: HealthStatus
}

export function HealthBadge({ status }: HealthBadgeProps) {
  const style = healthStyles[status]
  const Icon = style.icon

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold ${style.className}`}
    >
      <Icon aria-hidden="true" className="h-3 w-3" />
      {style.label}
    </span>
  )
}
