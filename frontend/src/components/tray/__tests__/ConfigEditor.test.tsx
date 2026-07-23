import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, jest } from '@jest/globals'
import { ConfigEditor } from '@/components/tray/ConfigEditor'
import { InstanceConfigUpdate, MutationResult } from '@/lib/trayApi'

const dryRun: MutationResult = {
  dry_run: true,
  applied: false,
  would_send: {
    operation: 'updateSolutionInstance',
    input: {
      configValues: [{ externalId: 'company-name', value: 'Acme' }],
    },
  },
}

describe('ConfigEditor', () => {
  it('blocks dry-run submission until required slots are set', async () => {
    const onDryRun = jest.fn(
      async (_update: InstanceConfigUpdate): Promise<MutationResult> => dryRun
    )
    const onApply = jest.fn(
      async (_update: InstanceConfigUpdate): Promise<void> => undefined
    )

    render(
      <ConfigEditor
        configSlots={[
          {
            externalId: 'company-name',
            title: 'Company name',
            required: true,
          },
        ]}
        onDryRun={onDryRun}
        onApply={onApply}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Review dry run' }))

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Company name is required'
    )
    expect(onDryRun).not.toHaveBeenCalled()
  })

  it('renders the dry-run diff before allowing apply', async () => {
    const onDryRun = jest.fn(
      async (_update: InstanceConfigUpdate): Promise<MutationResult> => dryRun
    )
    const onApply = jest.fn(
      async (_update: InstanceConfigUpdate): Promise<void> => undefined
    )

    render(
      <ConfigEditor
        configSlots={[
          {
            externalId: 'company-name',
            title: 'Company name',
            required: true,
          },
        ]}
        onDryRun={onDryRun}
        onApply={onApply}
      />
    )

    fireEvent.change(screen.getByLabelText(/Company name/), {
      target: { value: 'Acme' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Review dry run' }))

    expect(
      (await screen.findByLabelText('Dry-run diff')).textContent
    ).toContain('Will send')
    expect(screen.getByText(/company-name/)).toBeTruthy()
    expect(onApply).not.toHaveBeenCalled()

    fireEvent.click(
      screen.getByRole('button', { name: 'Apply to live instance' })
    )
    await waitFor(() => expect(onApply).toHaveBeenCalledTimes(1))
  })
})
