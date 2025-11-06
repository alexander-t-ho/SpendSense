import { useQuery } from '@tanstack/react-query'
import { fetchBudgetTracking } from '../services/api'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'
import { useState } from 'react'
import { X, CheckCircle, AlertCircle, XCircle } from 'lucide-react'

interface BudgetTrackingCardProps {
  userId: string
  month?: string
}

export default function BudgetTrackingCard({ userId, month }: BudgetTrackingCardProps) {
  const [isClosed, setIsClosed] = useState(false)

  const { data: tracking, isLoading, error } = useQuery({
    queryKey: ['budgetTracking', userId, month],
    queryFn: () => fetchBudgetTracking(userId, month),
    enabled: !!userId && !isClosed,
  })

  if (isClosed) {
    return null
  }

  if (isLoading) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-white">Loading budget tracking...</div>
      </div>
    )
  }

  if (error || !tracking) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-red-300">Failed to load budget tracking</div>
      </div>
    )
  }

  const percentageUsed = tracking.percentage_used || 0
  const remaining = tracking.remaining || 0
  const status = tracking.status || 'on_track'

  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'over_budget':
        return { color: 'red', icon: XCircle, text: 'Over Budget', bgColor: '#EF4444' }
      case 'warning':
        return { color: 'yellow', icon: AlertCircle, text: 'Warning', bgColor: '#F59E0B' }
      default:
        return { color: 'green', icon: CheckCircle, text: 'On Track', bgColor: '#10B981' }
    }
  }

  const statusInfo = getStatusInfo(status)
  const StatusIcon = statusInfo.icon

  const radialData = [{
    name: 'Used',
    value: Math.min(percentageUsed, 100),
    fill: statusInfo.bgColor
  }]

  return (
    <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-white mb-2">Budget Tracking</h1>
        <p className="text-white/80 text-sm">
          Monitor your spending against your monthly budget in real-time.
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

        {/* Status Badge */}
        <div className="flex items-center gap-2 mb-4">
          <StatusIcon className={`h-5 w-5 text-${statusInfo.color}-400`} />
          <span className={`text-sm font-medium text-${statusInfo.color}-400`}>
            {statusInfo.text}
          </span>
        </div>

        {/* Main Heading */}
        <h2 className="text-2xl font-semibold text-white mb-1">
          {percentageUsed.toFixed(1)}% of budget used
        </h2>

        {/* Timeframe Label */}
        <p className="text-xs uppercase tracking-wider text-white/60 mb-4">
          {tracking.month ? tracking.month.toUpperCase() : 'CURRENT MONTH'}
          {tracking.days_remaining !== undefined && ` • ${tracking.days_remaining} DAYS REMAINING`}
        </p>

        {/* Radial Progress */}
        <div className="relative flex items-center justify-center mb-6">
          <ResponsiveContainer width="100%" height={200}>
            <RadialBarChart
              innerRadius="60%"
              outerRadius="90%"
              data={radialData}
              startAngle={90}
              endAngle={-270}
            >
              <RadialBar dataKey="value" cornerRadius={10} fill={statusInfo.bgColor} />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute text-center">
            <p className="text-4xl font-bold text-white">{percentageUsed.toFixed(1)}%</p>
            <p className="text-sm text-white/70">Used</p>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white/10 rounded-lg p-4 border border-white/20">
            <p className="text-xs text-white/70 mb-1">Total Budget</p>
            <p className="text-lg font-bold text-white">
              ${tracking.total_budget?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'}
            </p>
          </div>
          <div className="bg-white/10 rounded-lg p-4 border border-white/20">
            <p className="text-xs text-white/70 mb-1">Total Spent</p>
            <p className="text-lg font-bold text-red-400">
              ${tracking.total_spent?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'}
            </p>
          </div>
          <div className="bg-white/10 rounded-lg p-4 border border-white/20">
            <p className="text-xs text-white/70 mb-1">Remaining</p>
            <p className={`text-lg font-bold ${remaining >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${Math.abs(remaining).toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </p>
          </div>
        </div>

        {/* Summary Text */}
        <p className="text-white/90 text-sm leading-relaxed">
          {remaining >= 0
            ? `You have $${Math.abs(remaining).toLocaleString('en-US', { maximumFractionDigits: 0 })} remaining this month. Keep up the good work!`
            : `You've exceeded your budget by $${Math.abs(remaining).toLocaleString('en-US', { maximumFractionDigits: 0 })}. Consider adjusting your spending for the remaining days.`
          }
        </p>
      </div>
    </div>
  )
}
