import { useQuery } from '@tanstack/react-query'
import { fetchWeeklyRecap } from '../services/api'

interface WeeklyRecapCardProps {
  userId: string
  weekStart?: string
}

export default function WeeklyRecapCard({ userId, weekStart }: WeeklyRecapCardProps) {
  const { data: recap, isLoading, error } = useQuery({
    queryKey: ['weeklyRecap', userId, weekStart],
    queryFn: () => fetchWeeklyRecap(userId, weekStart),
    enabled: !!userId,
  })

  if (isLoading) {
    return (
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-[#5D4037]">Loading your weekly recap...</div>
      </div>
    )
  }

  if (error || !recap) {
    return (
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-red-600">Failed to load weekly recap</div>
      </div>
    )
  }

  const formatAmount = (amount: number): string => {
    if (amount === 0) return '$0'
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

  const formatDayLabel = (dateStr: string): string => {
    if (!dateStr) return ''
    // Parse date string (YYYY-MM-DD) and create date in local timezone
    // to avoid timezone conversion issues
    const [year, month, day] = dateStr.split('-').map(Number)
    const date = new Date(year, month - 1, day) // month is 0-indexed in JS Date
    const monthName = date.toLocaleDateString('en-US', { month: 'short' })
    const dayNum = date.getDate()
    return `${monthName} ${dayNum}`
  }

  const dailySpending = recap.daily_spending || []
  const totalSpending = recap.total_spending || 0
  const topCategory = recap.top_category || 'dining'
  const summaryText = recap.summary_text || ''

  return (
    <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-[#5D4037] mb-2">Weekly recaps</h1>
        <p className="text-[#556B2F]/80 text-sm">
          Your financial life, summarized daily—stay in sync with the markets, the news, and your money.
        </p>
      </div>

      {/* Main Card */}
      <div className="relative bg-white/90 backdrop-blur-md rounded-xl border border-[#D4C4B0]/50 p-6 shadow-xl">
          {/* Progress Indicators */}
          <div className="flex justify-center gap-2 mb-4">
            <div className="w-2 h-1 bg-[#556B2F] rounded-full" />
            <div className="w-2 h-1 bg-[#E8F5E9] rounded-full border border-[#C8E6C9]" />
            <div className="w-2 h-1 bg-[#E8F5E9] rounded-full border border-[#C8E6C9]" />
            <div className="w-2 h-1 bg-[#E8F5E9] rounded-full border border-[#C8E6C9]" />
            <div className="w-2 h-1 bg-[#E8F5E9] rounded-full border border-[#C8E6C9]" />
          </div>

          {/* Main Heading */}
          <h2 className="text-2xl font-semibold text-[#5D4037] mb-1">
            You spent the most on {topCategory}.
          </h2>

          {/* Timeframe Label */}
          <p className="text-xs uppercase tracking-wider text-[#556B2F]/60 mb-4">
            SPEND LAST 7 DAYS
          </p>

          {/* Total Spending */}
          <div className="text-4xl font-bold text-[#5D4037] mb-6 text-center">
            ${totalSpending.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>

          {/* 7-Day Breakdown */}
          <div className="flex gap-2 mb-8">
            {/* Always show exactly 7 days - backend should always return 7 days */}
            {Array.from({ length: 7 }).map((_, index) => {
              const day = dailySpending[index] || { day: index + 1, date: '', amount: 0, is_current_day: false }
              const isCurrentDay = day.is_current_day || (index === 6 && !day.date) // Day 7 is current day
              const amount = day.amount || 0
              
              // Calculate date if not provided (shouldn't happen, but fallback)
              let dateStr = day.date
              if (!dateStr && recap.week_start) {
                const weekStart = new Date(recap.week_start)
                const dayDate = new Date(weekStart)
                dayDate.setDate(weekStart.getDate() + index)
                dateStr = dayDate.toISOString().split('T')[0]
              }
              
              const dayLabel = dateStr ? formatDayLabel(dateStr) : `Day ${day.day || index + 1}`
              
              return (
                <div
                  key={day.day || index}
                  className={`flex-1 rounded-lg p-3 transition-all ${
                    isCurrentDay
                      ? 'bg-[#556B2F] text-white'
                      : 'bg-[#E8F5E9]/80 text-[#5D4037] border border-[#C8E6C9]'
                  }`}
                >
                  <div className="text-xs font-medium mb-1 opacity-70 text-center">
                    {dayLabel}
                  </div>
                  <div className={`text-sm font-semibold text-center ${
                    isCurrentDay ? 'text-white' : 'text-[#5D4037]'
                  }`}>
                    {formatAmount(amount)}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Summary Text */}
          <p className="text-[#5D4037]/90 text-sm leading-relaxed">
            {summaryText || 'No spending data available for this period.'}
          </p>
        </div>
    </div>
  )
}
