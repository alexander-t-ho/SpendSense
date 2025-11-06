import { useQuery } from '@tanstack/react-query'
import { fetchBudgetTracking } from '../services/api'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'
import { CheckCircle, AlertCircle, XCircle, Target } from 'lucide-react'

interface BudgetTrackingCardProps {
  userId: string
  month?: string
}

export default function BudgetTrackingCard({ userId, month }: BudgetTrackingCardProps) {
  const { data: tracking, isLoading, error } = useQuery({
    queryKey: ['budgetTracking', userId, month],
    queryFn: () => fetchBudgetTracking(userId, month),
    enabled: !!userId,
  })

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error || !tracking) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-red-500">Failed to load budget tracking</p>
      </div>
    )
  }

  const percentageUsed = tracking.percentage_used || 0
  const remaining = tracking.remaining || 0
  const status = tracking.status || 'on_track'

  // Get status color and icon
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'over_budget':
        return { color: 'red', icon: XCircle, bg: 'bg-red-50', text: 'Over Budget' }
      case 'warning':
        return { color: 'yellow', icon: AlertCircle, bg: 'bg-yellow-50', text: 'Warning' }
      default:
        return { color: 'green', icon: CheckCircle, bg: 'bg-green-50', text: 'On Track' }
    }
  }

  const statusInfo = getStatusInfo(status)
  const StatusIcon = statusInfo.icon

  // Prepare radial chart data
  const radialData = [
    {
      name: 'Used',
      value: Math.min(percentageUsed, 100),
      fill: status === 'over_budget' ? '#EF4444' : status === 'warning' ? '#F59E0B' : '#10B981'
    }
  ]

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Target className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-900">Budget Tracking</h3>
        </div>
        <div className="flex items-center space-x-2">
          <StatusIcon className={`h-5 w-5 text-${statusInfo.color}-500`} />
          <span className={`text-sm font-medium text-${statusInfo.color}-600`}>{statusInfo.text}</span>
        </div>
      </div>

      {/* Month Info */}
      <div className="text-sm text-gray-500 mb-6">
        {tracking.month || 'Current month'}
        {tracking.days_remaining !== undefined && (
          <span className="ml-2">• {tracking.days_remaining} days remaining</span>
        )}
      </div>

      {/* Overall Progress */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Radial Progress Gauge */}
        <div className="flex items-center justify-center">
          <ResponsiveContainer width="100%" height={200}>
            <RadialBarChart
              innerRadius="60%"
              outerRadius="90%"
              data={radialData}
              startAngle={90}
              endAngle={-270}
            >
              <RadialBar dataKey="value" cornerRadius={10} fill={radialData[0].fill} />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute text-center">
            <p className="text-3xl font-bold text-gray-900">{percentageUsed.toFixed(1)}%</p>
            <p className="text-sm text-gray-500">Used</p>
          </div>
        </div>

        {/* Budget Details */}
        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Total Budget</p>
            <p className="text-2xl font-bold text-gray-900">
              ${tracking.total_budget?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Total Spent</p>
            <p className="text-2xl font-bold text-red-600">
              ${tracking.total_spent?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Remaining</p>
            <p className={`text-2xl font-bold ${remaining >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${Math.abs(remaining).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      {tracking.category_breakdown && Object.keys(tracking.category_breakdown).length > 0 && (
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Budget by Category</h4>
          <div className="space-y-3">
            {Object.entries(tracking.category_breakdown)
              .sort((a, b) => (b[1] as any).budget - (a[1] as any).budget)
              .map(([category, data]: [string, any]) => {
                const catPercentage = data.budget > 0 ? (data.spent / data.budget) * 100 : 0
                const catStatus = catPercentage > 100 ? 'over' : catPercentage > 80 ? 'warning' : 'on_track'
                return (
                  <div key={category}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600 capitalize">{category.replace('_', ' ')}</span>
                      <span className="text-sm font-semibold text-gray-900">
                        ${data.spent?.toFixed(2) || '0.00'} / ${data.budget?.toFixed(2) || '0.00'}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          catStatus === 'over' ? 'bg-red-500' : catStatus === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(catPercentage, 100)}%` }}
                      />
                    </div>
                  </div>
                )
              })}
          </div>
        </div>
      )}
    </div>
  )
}

