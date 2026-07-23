'use client'

import { FormEvent, useState } from 'react'
import {
  InstanceConfigUpdate,
  MutationResult,
} from '@/lib/trayApi'

export interface ConfigSlotDefinition {
  externalId?: string
  id?: string
  key?: string
  name?: string
  title?: string
  label?: string
  type?: string
  inputType?: string
  required?: boolean
  value?: unknown
  options?: Array<string | { label?: string; value: string }>
}

export interface AuthSlotDefinition {
  externalId?: string
  id?: string
  key?: string
  name?: string
  title?: string
  label?: string
  status?: string
  configured?: boolean
  authId?: string
  auth_id?: string
  authenticationId?: string
  value?: string
}

interface ConfigEditorProps {
  configSlots: ConfigSlotDefinition[]
  authSlots?: AuthSlotDefinition[]
  onDryRun: (
    update: InstanceConfigUpdate
  ) => Promise<MutationResult> | MutationResult
  onApply: (
    update: InstanceConfigUpdate
  ) => Promise<MutationResult | void> | MutationResult | void
  onReconnect?: (externalId: string) => void
}

function slotId(slot: ConfigSlotDefinition | AuthSlotDefinition): string {
  return String(slot.externalId || slot.id || slot.key || '')
}

function slotLabel(slot: ConfigSlotDefinition | AuthSlotDefinition): string {
  return String(
    slot.title || slot.label || slot.name || slotId(slot) || 'Unnamed slot'
  )
}

function initialValues(
  slots: ConfigSlotDefinition[]
): Record<string, string> {
  return Object.fromEntries(
    slots
      .map((slot) => [slotId(slot), slot.value == null ? '' : String(slot.value)])
      .filter(([id]) => Boolean(id))
  )
}

function optionValue(
  option: string | { label?: string; value: string }
): string {
  return typeof option === 'string' ? option : option.value
}

function optionLabel(
  option: string | { label?: string; value: string }
): string {
  return typeof option === 'string' ? option : option.label || option.value
}

function authId(slot: AuthSlotDefinition): string {
  return String(
    slot.authId || slot.auth_id || slot.authenticationId || slot.value || ''
  )
}

export function ConfigEditor({
  configSlots,
  authSlots = [],
  onDryRun,
  onApply,
  onReconnect,
}: ConfigEditorProps) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    initialValues(configSlots)
  )
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [preview, setPreview] = useState<MutationResult | null>(null)
  const [isWorking, setIsWorking] = useState(false)
  const [requestError, setRequestError] = useState<string | null>(null)

  const buildUpdate = (): InstanceConfigUpdate => ({
    config_values: configSlots
      .map((slot) => ({
        externalId: slotId(slot),
        value: values[slotId(slot)] || '',
      }))
      .filter((item) => Boolean(item.externalId)),
    auth_values: authSlots
      .map((slot) => ({
        externalId: slotId(slot),
        authId: authId(slot),
      }))
      .filter((item) => Boolean(item.externalId && item.authId)),
  })

  const validate = (): boolean => {
    const nextErrors = Object.fromEntries(
      configSlots
        .filter((slot) => slot.required && !values[slotId(slot)]?.trim())
        .map((slot) => [slotId(slot), `${slotLabel(slot)} is required`])
    )
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const handlePreview = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!validate()) return
    setIsWorking(true)
    setRequestError(null)
    try {
      setPreview(await onDryRun(buildUpdate()))
    } catch (caught) {
      setRequestError(
        caught instanceof Error ? caught.message : 'Could not prepare dry run'
      )
    } finally {
      setIsWorking(false)
    }
  }

  const handleApply = async () => {
    if (!validate()) return
    setIsWorking(true)
    setRequestError(null)
    try {
      await onApply(buildUpdate())
      setPreview(null)
    } catch (caught) {
      setRequestError(
        caught instanceof Error ? caught.message : 'Could not apply configuration'
      )
    } finally {
      setIsWorking(false)
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold text-slate-950">
          Instance configuration
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Review the exact live payload before applying it.
        </p>
      </div>

      <form className="mt-5 space-y-5" onSubmit={handlePreview} noValidate>
        {configSlots.length === 0 ? (
          <p className="text-sm text-slate-500">
            This Solution has no configuration slots.
          </p>
        ) : (
          configSlots.map((slot) => {
            const id = slotId(slot)
            const type = String(slot.type || slot.inputType || 'text').toLowerCase()
            const options = slot.options || []
            const controlClasses =
              'mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500'
            return (
              <div key={id}>
                <label
                  htmlFor={`config-${id}`}
                  className="text-sm font-medium text-slate-800"
                >
                  {slotLabel(slot)}
                  {slot.required ? (
                    <span className="ml-1 text-red-600" aria-hidden="true">
                      *
                    </span>
                  ) : null}
                </label>
                {options.length > 0 || type === 'select' ? (
                  <select
                    id={`config-${id}`}
                    value={values[id] || ''}
                    aria-invalid={Boolean(errors[id])}
                    className={controlClasses}
                    onChange={(event) => {
                      setValues((current) => ({
                        ...current,
                        [id]: event.target.value,
                      }))
                      setPreview(null)
                    }}
                  >
                    <option value="">Select a value</option>
                    {options.map((option) => (
                      <option key={optionValue(option)} value={optionValue(option)}>
                        {optionLabel(option)}
                      </option>
                    ))}
                  </select>
                ) : type.includes('json') ||
                  type.includes('map') ||
                  type.includes('object') ? (
                  <textarea
                    id={`config-${id}`}
                    value={values[id] || ''}
                    aria-invalid={Boolean(errors[id])}
                    className={`${controlClasses} min-h-28 font-mono`}
                    onChange={(event) => {
                      setValues((current) => ({
                        ...current,
                        [id]: event.target.value,
                      }))
                      setPreview(null)
                    }}
                  />
                ) : (
                  <input
                    id={`config-${id}`}
                    type={type === 'number' ? 'number' : 'text'}
                    value={values[id] || ''}
                    aria-invalid={Boolean(errors[id])}
                    className={controlClasses}
                    onChange={(event) => {
                      setValues((current) => ({
                        ...current,
                        [id]: event.target.value,
                      }))
                      setPreview(null)
                    }}
                  />
                )}
                {errors[id] ? (
                  <p role="alert" className="mt-1 text-sm text-red-700">
                    {errors[id]}
                  </p>
                ) : null}
              </div>
            )
          })
        )}

        {authSlots.length > 0 ? (
          <fieldset className="space-y-3 border-t border-slate-200 pt-5">
            <legend className="text-sm font-semibold text-slate-900">
              Authentication connections
            </legend>
            {authSlots.map((slot) => {
              const id = slotId(slot)
              const connected = slot.configured !== false && slot.status !== 'broken'
              return (
                <div
                  key={id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-200 px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {slotLabel(slot)}
                    </p>
                    <p className="text-xs text-slate-500">
                      {connected ? 'Connected' : 'Connection required'}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onReconnect?.(id)}
                    className="text-sm font-semibold text-indigo-700 hover:text-indigo-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    Reconnect via wizard
                  </button>
                </div>
              )
            })}
          </fieldset>
        ) : null}

        <button
          type="submit"
          disabled={isWorking}
          className="inline-flex rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isWorking ? 'Preparing…' : 'Review dry run'}
        </button>
      </form>

      {requestError ? (
        <p role="alert" className="mt-4 text-sm text-red-700">
          {requestError}
        </p>
      ) : null}

      {preview ? (
        <div
          aria-label="Dry-run diff"
          className="mt-5 rounded-md border border-amber-200 bg-amber-50 p-4"
        >
          <h3 className="font-semibold text-amber-950">Dry-run diff</h3>
          <p className="mt-1 text-sm text-amber-900">Will send</p>
          <pre className="mt-2 max-h-72 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">
            {JSON.stringify(preview.would_send, null, 2)}
          </pre>
          <button
            type="button"
            disabled={isWorking}
            onClick={() => void handleApply()}
            className="mt-3 inline-flex rounded-md bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-50"
          >
            Apply to live instance
          </button>
        </div>
      ) : null}
    </section>
  )
}
