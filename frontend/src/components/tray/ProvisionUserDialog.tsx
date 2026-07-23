'use client'

import { FormEvent, useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { Plus, X } from 'lucide-react'
import {
  MutationResult,
  ProvisionUserInput,
} from '@/lib/trayApi'

interface ProvisionUserDialogProps {
  onProvision: (
    user: ProvisionUserInput,
    confirm: boolean
  ) => Promise<MutationResult>
}

export function ProvisionUserDialog({
  onProvision,
}: ProvisionUserDialogProps) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [externalUserId, setExternalUserId] = useState('')
  const [preview, setPreview] = useState<MutationResult | null>(null)
  const [isWorking, setIsWorking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const input = { name: name.trim(), externalUserId: externalUserId.trim() }

  const previewProvision = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setIsWorking(true)
    try {
      setPreview(await onProvision(input, false))
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : 'Could not prepare dry run'
      )
    } finally {
      setIsWorking(false)
    }
  }

  const applyProvision = async () => {
    setError(null)
    setIsWorking(true)
    try {
      await onProvision(input, true)
      setOpen(false)
      setName('')
      setExternalUserId('')
      setPreview(null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Provisioning failed')
    } finally {
      setIsWorking(false)
    }
  }

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen)
        if (!nextOpen) {
          setPreview(null)
          setError(null)
        }
      }}
    >
      <Dialog.Trigger asChild>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <Plus aria-hidden="true" className="h-4 w-4" />
          Provision end user
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-slate-950/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[90vh] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-auto rounded-lg bg-white p-6 shadow-xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="text-lg font-semibold text-slate-950">
                Provision Tray end user
              </Dialog.Title>
              <Dialog.Description className="mt-1 text-sm text-slate-500">
                Preview the master-token operations before creating the user.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Close"
                className="rounded p-1 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <X aria-hidden="true" className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>

          <form className="mt-5 space-y-4" onSubmit={previewProvision}>
            <div>
              <label
                htmlFor="tray-user-name"
                className="text-sm font-medium text-slate-800"
              >
                Name
              </label>
              <input
                id="tray-user-name"
                required
                value={name}
                onChange={(event) => {
                  setName(event.target.value)
                  setPreview(null)
                }}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label
                htmlFor="tray-external-user-id"
                className="text-sm font-medium text-slate-800"
              >
                External user ID
              </label>
              <input
                id="tray-external-user-id"
                required
                value={externalUserId}
                onChange={(event) => {
                  setExternalUserId(event.target.value)
                  setPreview(null)
                }}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <button
              type="submit"
              disabled={isWorking || !input.name || !input.externalUserId}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              Review dry run
            </button>
          </form>

          {error ? (
            <p role="alert" className="mt-4 text-sm text-red-700">
              {error}
            </p>
          ) : null}

          {preview ? (
            <div className="mt-5 rounded-md border border-amber-200 bg-amber-50 p-4">
              <p className="text-sm font-semibold text-amber-950">Will send</p>
              <pre className="mt-2 max-h-48 overflow-auto rounded bg-slate-950 p-3 text-xs text-white">
                {JSON.stringify(preview.would_send, null, 2)}
              </pre>
              <button
                type="button"
                disabled={isWorking}
                onClick={() => void applyProvision()}
                className="mt-3 rounded-md bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-50"
              >
                Confirm provisioning
              </button>
            </div>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
