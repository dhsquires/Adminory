'use client'

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { TimeseriesPoint, TraySource } from '@/types/tray'
import { SourceBadge } from './SourceBadge'

interface ExecutionsChartProps {
  data: TimeseriesPoint[]
  source?: TraySource
}

export function ExecutionsChart({
  data,
  source = 'unofficial',
}: ExecutionsChartProps) {
  const chartData = data.map((point, index) => ({
    label:
      point.time || point.date || point.timestamp || `Point ${index + 1}`,
    executions:
      point.value ?? point.executions ?? point.count ?? 0,
  }))

  return (
    <section
      aria-labelledby="executions-heading"
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div className="flex items-center gap-2">
        <h2
          id="executions-heading"
          className="text-lg font-semibold text-slate-950"
        >
          Executions
        </h2>
        <SourceBadge source={source} />
      </div>
      <p className="mt-1 text-sm text-slate-500">Execution volume over time</p>

      {chartData.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-sm text-slate-500">
          No execution timeseries is available.
        </div>
      ) : (
        <div className="mt-5 h-64 w-full" aria-label="Execution volume chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis
                dataKey="label"
                tick={{ fill: '#64748b', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fill: '#64748b', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="executions"
                stroke="#4f46e5"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  )
}
