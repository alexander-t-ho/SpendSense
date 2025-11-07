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
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-[#5D4037]">Loading net worth...</div>
      </div>
    )
  }

  if (!netWorth) {
    return (
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-red-600">Failed to load net worth data</div>
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
    <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-[#5D4037] mb-2">Net Worth Overview</h1>
        <p className="text-[#556B2F]/80 text-sm">
          Track your financial position and growth over time.
        </p>
      </div>

      {/* Main Card */}
      <div className="relative bg-white/90 backdrop-blur-md rounded-xl border border-[#D4C4B0]/50 p-6 shadow-xl">
        {/* Close Button */}
        <button
          onClick={() => setIsClosed(true)}
          className="absolute top-4 right-4 text-[#5D4037] hover:text-[#556B2F] transition-colors z-10"
          aria-label="Close"
        >
          <X size={20} />
        </button>

        {/* Main Heading */}
        <h2 className="text-2xl font-semibold text-[#5D4037] mb-1">
          Your net worth is {formatAmount(netWorthValue)}
        </h2>

        {/* Timeframe Label */}
        <p className="text-xs uppercase tracking-wider text-[#556B2F]/60 mb-4">
          {period.toUpperCase()} VIEW
        </p>

        {/* Net Worth Value */}
        <div className="text-4xl font-bold text-[#5D4037] mb-6 text-center">
          ${netWorthValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>

        {/* Change Indicator */}
        {changeAmount !== 0 && (
          <div className={`flex items-center gap-2 mb-6 justify-center ${isPositive ? 'text-[#556B2F]' : 'text-red-600'}`}>
            {isPositive ? <ArrowUp size={20} /> : <ArrowDown size={20} />}
            <span className="text-lg font-semibold">
              {isPositive ? '+' : ''}{changePercent.toFixed(1)}% ({isPositive ? '+' : ''}${Math.abs(changeAmount).toLocaleString('en-US', { maximumFractionDigits: 2 })})
            </span>
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-[#E8F5E9] rounded-lg p-4 border border-[#C8E6C9]">
            <p className="text-xs text-[#556B2F] mb-1">Total Assets</p>
            <p className="text-xl font-bold text-[#556B2F]">
              ${totalAssets.toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="bg-[#E8F5E9] rounded-lg p-4 border border-[#C8E6C9]">
            <p className="text-xs text-[#556B2F] mb-1">Total Liabilities</p>
            <p className="text-xl font-bold text-red-600">
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
                    <stop offset="5%" stopColor="#556B2F" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#556B2F" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(93,64,55,0.1)" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fill: '#5D4037', fontSize: 12 }}
                  stroke="#5D4037"
                />
                <YAxis 
                  tick={{ fill: '#5D4037', fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                  stroke="#5D4037"
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(245, 230, 211, 0.95)', 
                    border: '1px solid #5D4037',
                    borderRadius: '8px',
                    color: '#5D4037'
                  }}
                  formatter={(value: number) => [`$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`, 'Net Worth']}
                />
                <Area 
                  type="monotone" 
                  dataKey="netWorth" 
                  stroke="#556B2F" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorNetWorth)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Summary Text */}
        <p className="text-[#5D4037]/90 text-sm leading-relaxed">
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
