import { useQuery } from '@tanstack/react-query'
import { fetchSpendingAnalysis } from '../services/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useState } from 'react'
import { X } from 'lucide-react'

interface SpendingAnalysisCardProps {
  userId: string
  months?: number
}

export default function SpendingAnalysisCard({ userId, months = 6 }: SpendingAnalysisCardProps) {
  const [isClosed, setIsClosed] = useState(false)
  
  const { data: analysis, isLoading, error } = useQuery({
    queryKey: ['spendingAnalysis', userId, months],
    queryFn: () => fetchSpendingAnalysis(userId, months),
    enabled: !!userId && !isClosed,
  })

  if (isClosed) {
    return null
  }

  if (isLoading) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-white">Loading spending analysis...</div>
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-red-300">Failed to load spending analysis</div>
      </div>
    )
  }

  const chartData = analysis.monthly_breakdown?.map((month: any) => ({
    month: new Date(month.month).toLocaleDateString('en-US', { month: 'short' }),
    spending: Math.abs(month.total_spending || 0),
    income: month.total_income || 0,
  })) || []

  const totalSpending = analysis.total_spending || 0
  const avgMonthly = analysis.average_monthly_spending || 0
  const topInsight = analysis.insights?.[0] || 'Your spending trends are consistent.'

  return (
    <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-white mb-2">6-Month Spending Analysis</h1>
        <p className="text-white/80 text-sm">
          Track your spending patterns and income trends over time.
        </p>
      </div>

      {/* Main Card */}
      <div className="relative bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 shadow-xl">
        {/* Close Button */}
        <button
          onClick={() => setIsClosed(true)}
          className="absolute top-4 right-4 text-white hover:text-white/70 transition-colors z-10"
          aria-label="Close"
        >
          <X size={20} />
        </button>

        {/* Main Heading */}
        <h2 className="text-2xl font-semibold text-white mb-1">
          Total spending: ${Math.abs(totalSpending).toLocaleString('en-US', { maximumFractionDigits: 0 })}
        </h2>

        {/* Timeframe Label */}
        <p className="text-xs uppercase tracking-wider text-white/60 mb-4">
          LAST {months} MONTHS
        </p>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white/10 rounded-lg p-4 border border-white/20">
            <p className="text-xs text-white/70 mb-1">Average Monthly</p>
            <p className="text-2xl font-bold text-white">
              ${Math.abs(avgMonthly).toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="bg-white/10 rounded-lg p-4 border border-white/20">
            <p className="text-xs text-white/70 mb-1">Income Stability</p>
            <p className="text-lg font-semibold text-white">
              {analysis.income_stability?.stability_level || 'Unknown'}
            </p>
          </div>
        </div>

        {/* Chart */}
        {chartData.length > 0 && (
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }}
                  stroke="rgba(255,255,255,0.3)"
                />
                <YAxis 
                  tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`}
                  stroke="rgba(255,255,255,0.3)"
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                  formatter={(value: number, name: string) => [
                    `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
                    name === 'spending' ? 'Spending' : 'Income'
                  ]}
                />
                <Legend 
                  wrapperStyle={{ color: 'rgba(255,255,255,0.8)' }}
                  iconType="line"
                />
                <Line 
                  type="monotone" 
                  dataKey="spending" 
                  stroke="#EF4444" 
                  strokeWidth={2}
                  name="Spending"
                  dot={{ r: 3, fill: '#EF4444' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="income" 
                  stroke="#10B981" 
                  strokeWidth={2}
                  name="Income"
                  dot={{ r: 3, fill: '#10B981' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Summary Text */}
        <p className="text-white/90 text-sm leading-relaxed">
          {topInsight}
        </p>
      </div>
    </div>
  )
}
