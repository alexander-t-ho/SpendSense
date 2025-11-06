import { useQuery } from '@tanstack/react-query'
import { fetchNetWorth, fetchNetWorthHistory } from '../services/api'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useState } from 'react'
import { X, ArrowUp, ArrowDown } from 'lucide-react'

interface NetWorthRecapCardProps {
  userId: string
  period?: 'week' | 'month'
}

export default function NetWorthRecapCard({ userId, period = 'month' }: NetWorthRecapCardProps) {
  const [isClosed, setIsClosed] = useState(false)

  const { data: netWorth, isLoading } = useQuery({
    queryKey: ['netWorth', userId, period],
    queryFn: () => fetchNetWorth(userId, period),
    enabled: !!userId && !isClosed,
  })

  const { data: history } = useQuery({
    queryKey: ['netWorthHistory', userId, period],
    queryFn: () => fetchNetWorthHistory(userId, period),
    enabled: !!userId && !isClosed,
  })

  if (isClosed) {
    return null
  }

  if (isLoading) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-white">Loading net worth...</div>
      </div>
    )
  }

  if (!netWorth) {
    return (
      <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
        <div className="text-red-300">Failed to load net worth data</div>
      </div>
    )
  }

  const current = netWorth.current || {}
  const netWorthValue = current.net_worth || 0
  const totalAssets = current.total_assets || 0
  const totalLiabilities = current.total_liabilities || 0

  // Calculate change from history
  const historyData = history?.history || []
  let changeAmount = 0
  let changePercent = 0
  if (historyData.length >= 2) {
    const first = historyData[0].net_worth
    const last = historyData[historyData.length - 1].net_worth
    changeAmount = last - first
    changePercent = first > 0 ? ((last - first) / first) * 100 : 0
  }

  const isPositive = changeAmount >= 0

  // Prepare chart data
  const chartData = historyData.map((point: any) => ({
    date: new Date(point.snapshot_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    netWorth: point.net_worth,
  }))

  const formatAmount = (amount: number): string => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`
    }
    if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(1)}k`
    }
    return `$${Math.round(amount)}`
  }

  return (
    <div className="relative bg-gradient-to-b from-purple-900 via-blue-900 to-blue-950 rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-white mb-2">Net Worth Overview</h1>
        <p className="text-white/80 text-sm">
          Track your financial position and growth over time.
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
          Your net worth is {formatAmount(netWorthValue)}
        </h2>

        {/* Timeframe Label */}
        <p className="text-xs uppercase tracking-wider text-white/60 mb-4">
          {period.toUpperCase()} VIEW
        </p>

        {/* Net Worth Value */}
        <div className="text-4xl font-bold text-white mb-6">
          ${netWorthValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>

        {/* Change Indicator */}
        {changeAmount !== 0 && (
          <div className={`flex items-center gap-2 mb-6 ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? <ArrowUp size={20} /> : <ArrowDown size={20} />}
            <span className="text-lg font-semibold">
              {isPositive ? '+' : ''}{changePercent.toFixed(1)}% ({isPositive ? '+' : ''}${Math.abs(changeAmount).toLocaleString('en-US', { maximumFractionDigits: 2 })})
            </span>
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white/10 rounded-lg p-4 border border-white/20">
            <p className="text-xs text-white/70 mb-1">Total Assets</p>
            <p className="text-xl font-bold text-green-400">
              ${totalAssets.toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="bg-white/10 rounded-lg p-4 border border-white/20">
            <p className="text-xs text-white/70 mb-1">Total Liabilities</p>
            <p className="text-xl font-bold text-red-400">
              ${totalLiabilities.toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </p>
          </div>
        </div>

        {/* Chart */}
        {chartData.length > 0 && (
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorNetWorth" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FFFFFF" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#FFFFFF" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }}
                  stroke="rgba(255,255,255,0.3)"
                />
                <YAxis 
                  tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                  stroke="rgba(255,255,255,0.3)"
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                  formatter={(value: number) => [`$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`, 'Net Worth']}
                />
                <Area 
                  type="monotone" 
                  dataKey="netWorth" 
                  stroke="#FFFFFF" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorNetWorth)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Summary Text */}
        <p className="text-white/90 text-sm leading-relaxed">
          {isPositive 
            ? `Your net worth increased by ${changePercent.toFixed(1)}% over the last ${period}. Keep up the great work!`
            : changeAmount < 0
            ? `Your net worth decreased by ${Math.abs(changePercent).toFixed(1)}% over the last ${period}. Consider reviewing your spending habits.`
            : 'Your net worth is stable. Maintain consistent saving habits to continue growing.'
          }
        </p>
      </div>
    </div>
  )
}
