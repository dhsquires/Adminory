import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from '@jest/globals'
import { TriageQueue } from '../TriageQueue'
import { TriageSignal } from '@/types/tray'

const criticalSignal: TriageSignal = {
  kind: 'auth_broken',
  instance_id: 'instance-critical',
  solution_id: 'solution-1',
  user_id: 'user-1',
  title: 'Authentication is blocked',
  reason: 'The required authentication slot is invalid.',
  severity: 'blocked',
  users_at_risk: 4,
  executions_at_risk: 30,
  blast_radius: 34,
  source: 'official',
}

const deadInstallSignal: TriageSignal = {
  kind: 'dead_install',
  instance_id: 'instance-dead',
  solution_id: 'solution-2',
  user_id: 'user-2',
  title: 'Install was never enabled',
  reason: 'The instance has never reached an enabled state.',
  severity: 'dead_install',
  users_at_risk: 1,
  executions_at_risk: 0,
  blast_radius: 1,
  source: 'official',
}

describe('TriageQueue', () => {
  it('preserves the ranked signal order supplied by the caller', () => {
    render(
      <TriageQueue signals={[criticalSignal, deadInstallSignal]} />
    )

    const rows = screen.getAllByRole('listitem')
    expect(within(rows[0]).getByText('Blocked')).toBeTruthy()
    expect(within(rows[1]).getByText('Dead install')).toBeTruthy()
  })
})
