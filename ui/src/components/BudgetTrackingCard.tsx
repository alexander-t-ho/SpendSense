import { useQuery } from '@tanstack/react-query'
import { fetchBudgetTracking } from '../services/api'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'
import { Target, CheckCircle, AlertCircle, XCircle, DollarSign } from 'lucide-react'
import FinancialTrackingFeatureTemplate, { KeyMetric } from './FinancialTrackingFeatureTemplate'

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

  if (isLoading || error || !tracking) {
    return (
      <FinancialTrackingFeatureTemplate
        title="Budget Tracking"
        icon={Target}
        iconColor="blue"
        isLoading={isLoading}
        error={error ? 'Failed to load budget tracking' : null}
      />
    )
  }

  const percentageUsed = tracking.percentage_used || 0
  const remaining = tracking.remaining || 0
  const status = tracking.status || 'on_track'

  // Get status color and icon
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'over_budget':
        return { color: 'red' as const, icon: XCircle, text: 'Over Budget' }
      case 'warning':
        return { color: 'yellow' as const, icon: AlertCircle, text: 'Warning' }
      default:
        return { color: 'green' as const, icon: CheckCircle, text: 'On Track' }
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

  const keyMetrics: KeyMetric[] = [
    {
      label: 'Total Budget',
      value: `$${tracking.total_budget?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}`,
      color: 'blue',
      icon: DollarSign,
    },
    {
      label: 'Total Spent',
      value: `$${tracking.total_spent?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}`,
      color: 'red',
      icon: DollarSign,
    },
    {
      label: 'Remaining',
      value: `$${Math.abs(remaining).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      color: remaining >= 0 ? 'green' : 'red',
      icon: Target,
    },
  ]

  return (
    <FinancialTrackingFeatureTemplate
      title="Budget Tracking"
      icon={Target}
      iconColor="blue"
      subtitle={tracking.month || 'Current month'}
      period={tracking.days_remaining !== undefined ? `${tracking.days_remaining} days remaining` : undefined}
      keyMetrics={keyMetrics}
      headerActions={
        <div className="flex items-center space-x-2">
          {statusInfo.color === 'red' && <StatusIcon className="h-5 w-5 text-red-500" />}
          {statusInfo.color === 'yellow' && <StatusIcon className="h-5 w-5 text-yellow-500" />}
          {statusInfo.color === 'green' && <StatusIcon className="h-5 w-5 text-green-500" />}
          {statusInfo.color === 'red' && <span className="text-sm font-medium text-red-600">{statusInfo.text}</span>}
          {statusInfo.color === 'yellow' && <span className="text-sm font-medium text-yellow-600">{statusInfo.text}</span>}
          {statusInfo.color === 'green' && <span className="text-sm font-medium text-green-600">{statusInfo.text}</span>}
        </div>
      }
      visualizations={
        <div className="relative flex items-center justify-center">
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
      }
      children={
        tracking.category_breakdown && Object.keys(tracking.category_breakdown).length > 0 ? (
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
        ) : null
      }
    />
  )
}

