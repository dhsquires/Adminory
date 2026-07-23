import { ArrowRight } from 'lucide-react'
import { Solution } from '@/types/tray'

const stages = [
  { key: 'authoring', label: 'Authoring' },
  { key: 'published', label: 'Published' },
  { key: 'active', label: 'Active' },
] as const

interface LifecycleFlowProps {
  solutions: Solution[]
}

export function LifecycleFlow({ solutions }: LifecycleFlowProps) {
  const countFor = (stage: (typeof stages)[number]['key']) =>
    solutions.filter((solution) => {
      const state = solution.state?.toLowerCase() || ''
      if (stage === 'active') {
        return state.includes('active') || solution.active_instances > 0
      }
      return state.includes(stage)
    }).length

  return (
    <section
      aria-labelledby="lifecycle-heading"
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
    >
      <h2 id="lifecycle-heading" className="text-lg font-semibold text-slate-950">
        Solution lifecycle
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Authoring state through activated estate
      </p>
      <ol className="mt-5 grid gap-3 sm:grid-cols-[1fr_auto_1fr_auto_1fr] sm:items-center">
        {stages.map((stage, index) => (
          <li key={stage.key} className="contents">
            <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {stage.label}
              </p>
              <p className="mt-1 font-mono text-xl font-semibold text-slate-950">
                {countFor(stage.key)}
              </p>
            </div>
            {index < stages.length - 1 ? (
              <ArrowRight
                aria-hidden="true"
                className="mx-auto hidden h-4 w-4 text-slate-400 sm:block"
              />
            ) : null}
          </li>
        ))}
      </ol>
    </section>
  )
}
