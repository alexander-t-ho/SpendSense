import { useQuery } from '@tanstack/react-query'
import { fetchSpendingAnalysis } from '../services/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, TooltipProps } from 'recharts'
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
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-[#5D4037]">Loading spending analysis...</div>
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-red-600">Failed to load spending analysis</div>
      </div>
    )
  }

  const chartData = analysis.monthly_breakdown?.map((month: any) => ({
    month: new Date(month.month + '-01').toLocaleDateString('en-US', { month: 'short' }),
    spending: Math.abs(month.spending || month.total_spending || 0),
    income: month.income || month.total_income || 0,
  })) || []

  const totalSpending = analysis.total_spending || 0
  const avgMonthly = analysis.average_monthly_spending || 0
  const topInsight = analysis.insights?.[0] || 'Your spending trends are consistent.'

  // Custom tooltip content to properly label spending vs income
  const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#F5E6D3] border border-[#5D4037] rounded-lg p-3 shadow-lg">
          <p className="text-[#5D4037] font-semibold mb-2">{label}</p>
          {payload.map((entry, index) => {
            const label = entry.dataKey === 'spending' ? 'Spending' : entry.dataKey === 'income' ? 'Income' : entry.name || 'Value';
            return (
              <p key={index} style={{ color: entry.color }} className="text-sm">
                {label}: ${(entry.value as number).toLocaleString('en-US', { maximumFractionDigits: 2 })}
              </p>
            );
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-[#5D4037] mb-2">6-Month Spending Analysis</h1>
        <p className="text-[#556B2F]/80 text-sm">
          Track your spending patterns and income trends over time.
        </p>
      </div>

      {/* Main Card */}
      <div className="relative bg-white/90 backdrop-blur-md rounded-xl border border-[#D4C4B0]/50 p-6 shadow-xl">
        {/* Close Button */}
        <button
          onClick={() => setIsClosed(true)}
          className="absolute top-4 right-4 text-[#5D4037] hover:text-[#8B6F47] transition-colors z-10"
          aria-label="Close"
        >
          <X size={20} />
        </button>

        {/* Main Heading */}
        <h2 className="text-2xl font-semibold text-[#5D4037] mb-1">
          Total spending: ${Math.abs(totalSpending).toLocaleString('en-US', { maximumFractionDigits: 0 })}
        </h2>

        {/* Timeframe Label */}
        <p className="text-xs uppercase tracking-wider text-[#556B2F]/60 mb-4">
          LAST {months} MONTHS
        </p>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-[#E8F5E9] rounded-lg p-4 border border-[#C8E6C9]">
            <p className="text-xs text-[#556B2F] mb-1">Average Monthly</p>
            <p className="text-2xl font-bold text-[#5D4037]">
              ${Math.abs(avgMonthly).toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="bg-[#E8F5E9] rounded-lg p-4 border border-[#C8E6C9]">
            <p className="text-xs text-[#556B2F] mb-1">Income Stability</p>
            <p className="text-lg font-semibold text-[#5D4037]">
              {analysis.income_stability?.stability_level || 'Unknown'}
            </p>
          </div>
        </div>

        {/* Chart */}
        {chartData.length > 0 && (
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(93,64,55,0.1)" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fill: '#5D4037', fontSize: 12 }}
                  stroke="#5D4037"
                />
                <YAxis 
                  tick={{ fill: '#5D4037', fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`}
                  stroke="#5D4037"
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  wrapperStyle={{ color: '#5D4037' }}
                  iconType="line"
                />
                <Line 
                  type="monotone" 
                  dataKey="spending" 
                  stroke="#DC2626" 
                  strokeWidth={3}
                  name="Spending"
                  dot={{ r: 4, fill: '#DC2626' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="income" 
                  stroke="#16A34A" 
                  strokeWidth={3}
                  name="Income"
                  dot={{ r: 4, fill: '#16A34A' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Summary Text */}
        <p className="text-[#5D4037]/90 text-sm leading-relaxed">
          {topInsight}
        </p>
      </div>
    </div>
  )
}
