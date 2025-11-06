import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchWeeklyRecap } from '../services/api'
import { X } from 'lucide-react'

interface WeeklyRecapCardProps {
  userId: string
  weekStart?: string
}

export default function WeeklyRecapCard({ userId, weekStart }: WeeklyRecapCardProps) {
  const [isClosed, setIsClosed] = useState(false)
  
  const { data: recap, isLoading, error } = useQuery({
    queryKey: ['weeklyRecap', userId, weekStart],
    queryFn: () => fetchWeeklyRecap(userId, weekStart),
    enabled: !!userId && !isClosed,
  })

  if (isClosed) {
    return null
  }

  if (isLoading) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-white">Loading your weekly recap...</div>
      </div>
    )
  }

  if (error || !recap) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-red-300">Failed to load weekly recap</div>
      </div>
    )
  }

  const formatAmount = (amount: number): string => {
    if (amount === 0) return '-'
    if (amount >= 1000) {
      const thousands = amount / 1000
      // Format like "$1.3k" for amounts like 1300
      if (thousands < 10) {
        return `$${thousands.toFixed(1)}k`
      }
      return `$${Math.round(thousands)}k`
    }
    return `$${Math.round(amount)}`
  }

  const dailySpending = recap.daily_spending || []
  const totalSpending = recap.total_spending || 0
  const topCategory = recap.top_category || 'dining'
  const summaryText = recap.summary_text || ''

  return (
    <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-white mb-2">Weekly recaps</h1>
        <p className="text-white/80 text-sm">
          Your financial life, summarized daily—stay in sync with the markets, the news, and your money.
        </p>
      </div>

      {/* Main Card */}
      <div className="relative bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 shadow-xl">
          {/* Progress Indicators */}
          <div className="flex justify-center gap-2 mb-4">
            <div className="w-2 h-1 bg-white rounded-full" />
            <div className="w-2 h-1 bg-white/30 rounded-full border border-white/30" />
            <div className="w-2 h-1 bg-white/30 rounded-full border border-white/30" />
            <div className="w-2 h-1 bg-white/30 rounded-full border border-white/30" />
            <div className="w-2 h-1 bg-white/30 rounded-full border border-white/30" />
          </div>

          {/* Close Button */}
          <button
            onClick={() => setIsClosed(true)}
            className="absolute top-4 right-4 text-white hover:text-white/70 transition-colors"
            aria-label="Close"
          >
            <X size={20} />
          </button>

          {/* Main Heading */}
          <h2 className="text-2xl font-semibold text-white mb-1">
            You spent the most on {topCategory}.
          </h2>

          {/* Timeframe Label */}
          <p className="text-xs uppercase tracking-wider text-white/60 mb-4">
            SPEND LAST 7 DAYS
          </p>

          {/* Total Spending */}
          <div className="text-4xl font-bold text-white mb-6">
            ${totalSpending.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>

          {/* 7-Day Breakdown */}
          <div className="flex gap-2 mb-8">
            {dailySpending.map((day: any, index: number) => {
              const isCurrentDay = day.is_current_day || index === dailySpending.length - 1
              const amount = day.amount || 0
              
              return (
                <div
                  key={day.day || index}
                  className={`flex-1 rounded-lg p-3 transition-all ${
                    isCurrentDay
                      ? 'bg-white text-gray-900'
                      : 'bg-gray-900/50 text-white border border-white/10'
                  }`}
                >
                  <div className="text-xs font-medium mb-1 opacity-70">
                    {day.day || index + 1}
                  </div>
                  <div className={`text-sm font-semibold ${
                    isCurrentDay ? 'text-gray-900' : 'text-white'
                  }`}>
                    {formatAmount(amount)}
                  </div>
                </div>
              )
            })}
            {/* Fill remaining days if we have less than 7 */}
            {dailySpending.length < 7 && Array.from({ length: 7 - dailySpending.length }).map((_, index) => (
              <div
                key={`empty-${index}`}
                className="flex-1 rounded-lg p-3 bg-gray-900/50 text-white border border-white/10"
              >
                <div className="text-xs font-medium mb-1 opacity-70">
                  {dailySpending.length + index + 1}
                </div>
                <div className="text-sm font-semibold text-white">-</div>
              </div>
            ))}
          </div>

          {/* Summary Text */}
          <p className="text-white/90 text-sm leading-relaxed">
            {summaryText || 'No spending data available for this period.'}
          </p>
        </div>
    </div>
  )
}
