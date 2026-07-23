import { AlertCircle, CheckCircle2 } from 'lucide-react'
import { TraySlot } from '@/types/tray'

interface SlotStatusTableProps {
  title: string
  slots: TraySlot[]
}

function slotLabel(slot: TraySlot, index: number): string {
  return String(
    slot.label || slot.name || slot.title || slot.key || slot.id || `Slot ${index + 1}`
  )
}

function isConfigured(slot: TraySlot): boolean {
  if (typeof slot.configured === 'boolean') return slot.configured
  const status = String(slot.status || '').toLowerCase()
  return !['missing', 'broken', 'expired', 'invalid', 'error'].includes(status)
}

export function SlotStatusTable({ title, slots }: SlotStatusTableProps) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
      </div>
      {slots.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-slate-500">
          No slots reported.
        </p>
      ) : (
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="px-4 py-3">
                Slot
              </th>
              <th scope="col" className="px-4 py-3">
                Required
              </th>
              <th scope="col" className="px-4 py-3">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {slots.map((slot, index) => {
              const configured = isConfigured(slot)
              return (
                <tr key={String(slot.id || slot.key || index)}>
                  <td className="px-4 py-3 font-medium text-slate-900">
                    {slotLabel(slot, index)}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {slot.required === false ? 'Optional' : 'Required'}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center gap-1 text-xs font-semibold ${
                        configured ? 'text-emerald-700' : 'text-red-700'
                      }`}
                    >
                      {configured ? (
                        <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
                      ) : (
                        <AlertCircle aria-hidden="true" className="h-4 w-4" />
                      )}
                      {configured ? String(slot.status || 'Configured') : String(slot.status || 'Missing')}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </section>
  )
}
