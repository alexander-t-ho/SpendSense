import { useQuery } from '@tanstack/react-query'
import { fetchNetWorth, fetchNetWorthHistory } from '../services/api'
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, ArrowUp, ArrowDown } from 'lucide-react'
import { useState } from 'react'
import FinancialTrackingFeatureTemplate, { KeyMetric } from './FinancialTrackingFeatureTemplate'

interface NetWorthRecapCardProps {
  userId: string
  period?: 'week' | 'month'
}

export default function NetWorthRecapCard({ userId, period = 'month' }: NetWorthRecapCardProps) {
  const [feedbackGiven, setFeedbackGiven] = useState<{ [key: string]: 'like' | 'dislike' | null }>({})

  const { data: netWorth, isLoading } = useQuery({
    queryKey: ['netWorth', userId, period],
    queryFn: () => fetchNetWorth(userId, period),
    enabled: !!userId,
  })

  const { data: history } = useQuery({
    queryKey: ['netWorthHistory', userId, period],
    queryFn: () => fetchNetWorthHistory(userId, period),
    enabled: !!userId,
  })

  const handleFeedback = async (insightId: string, feedbackType: 'like' | 'dislike') => {
    try {
      const { submitFeedback } = await import('../services/api')
      await submitFeedback(userId, insightId, 'net_worth', feedbackType)
      setFeedbackGiven({ ...feedbackGiven, [insightId]: feedbackType })
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }

  if (isLoading || !netWorth) {
    return (
      <FinancialTrackingFeatureTemplate
        title="Net Worth Overview"
        icon={DollarSign}
        iconColor="purple"
        isLoading={isLoading}
        error={!netWorth ? 'Failed to load net worth data' : null}
      />
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
    assets: point.total_assets,
    liabilities: point.total_liabilities,
  }))

  const keyMetrics: KeyMetric[] = [
    {
      label: 'Current Net Worth',
      value: `$${netWorthValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      color: 'purple',
      icon: DollarSign,
      trend: isPositive ? 'up' : changeAmount < 0 ? 'down' : 'neutral',
      trendValue: `${isPositive ? '+' : ''}${changePercent.toFixed(1)}%`,
    },
    {
      label: 'Total Assets',
      value: `$${totalAssets.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      color: 'green',
      icon: TrendingUp,
    },
    {
      label: 'Total Liabilities',
      value: `$${totalLiabilities.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      color: 'red',
      icon: TrendingDown,
    },
  ]

  return (
    <FinancialTrackingFeatureTemplate
      title="Net Worth Overview"
      icon={DollarSign}
      iconColor="purple"
      period={period === 'week' ? 'Weekly' : 'Monthly'}
      keyMetrics={keyMetrics}
      visualizations={
        chartData.length > 0 ? (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Net Worth Trend</h4>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorNetWorth" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                />
                <Tooltip 
                  formatter={(value: number) => [`$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, 'Net Worth']}
                  labelStyle={{ color: '#374151' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="netWorth" 
                  stroke="#8B5CF6" 
                  fillOpacity={1} 
                  fill="url(#colorNetWorth)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : null
      }
      children={
        <>
          {/* Change Amount Display */}
          {changeAmount !== 0 && (
            <div className="mb-4">
              <p className={`text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? <ArrowUp className="inline h-4 w-4" /> : <ArrowDown className="inline h-4 w-4" />}
                {' '}${Math.abs(changeAmount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 
                {' '}over the last {period}
              </p>
            </div>
          )}

          {/* Breakdown */}
          {current.breakdown && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Breakdown</h4>
              <div className="space-y-2">
                {Object.entries(current.breakdown).map(([category, amount]: [string, any]) => (
                  <div key={category} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{category.replace('_', ' ')}</span>
                    <span className="text-sm font-semibold text-gray-900">
                      ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      }
      actions={
        <div className="flex items-center justify-end space-x-2">
          <button
            onClick={() => handleFeedback('net_worth', 'like')}
            className={`flex items-center space-x-1 px-3 py-1 rounded text-sm ${
              feedbackGiven['net_worth'] === 'like' 
                ? 'bg-green-100 text-green-700' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <span>👍</span>
            <span>More like this</span>
          </button>
          <button
            onClick={() => handleFeedback('net_worth', 'dislike')}
            className={`flex items-center space-x-1 px-3 py-1 rounded text-sm ${
              feedbackGiven['net_worth'] === 'dislike' 
                ? 'bg-red-100 text-red-700' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <span>👎</span>
            <span>Less like this</span>
          </button>
        </div>
      }
    />
  )
}

