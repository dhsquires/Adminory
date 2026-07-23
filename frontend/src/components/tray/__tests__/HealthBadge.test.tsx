import { render, screen } from '@testing-library/react'
import { describe, expect, it } from '@jest/globals'
import { HealthBadge } from '../HealthBadge'
import { HealthStatus } from '@/types/tray'

describe('HealthBadge', () => {
  const cases: Array<[HealthStatus, string]> = [
    ['healthy', 'Healthy'],
    ['warning', 'Warning'],
    ['critical', 'Critical'],
    ['blocked', 'Blocked'],
    ['dead_install', 'Dead install'],
  ]

  it.each(cases)('maps %s to the %s label', (status, label) => {
    render(<HealthBadge status={status} />)

    expect(screen.getByText(label)).toBeTruthy()
  })
})
