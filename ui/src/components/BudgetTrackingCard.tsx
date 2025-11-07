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
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-[#5D4037]">Loading budget tracking...</div>
      </div>
    )
  }

  if (error || !tracking) {
    return (
      <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
        <div className="text-red-600">Failed to load budget tracking</div>
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
      case 'debt_concern':
        return { color: 'red', icon: XCircle, text: 'Debt Concern', bgColor: '#DC2626' }
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
        fill: statusInfo.color === 'red' ? '#dc2626' : statusInfo.color === 'yellow' ? '#8B6F47' : '#556B2F'
      }]

  return (
    <div className="relative bg-gradient-to-b from-[#F5E6D3] via-white to-[#F5E6D3] rounded-2xl overflow-hidden p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-serif text-[#5D4037] mb-2">Budget Tracking</h1>
        <p className="text-[#556B2F]/80 text-sm">
          Monitor your spending against your monthly budget in real-time.
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

        {/* Status Badge */}
        <div className="flex items-center gap-2 mb-4">
          <StatusIcon className={`h-5 w-5 ${statusInfo.color === 'red' ? 'text-red-600' : statusInfo.color === 'yellow' ? 'text-[#8B6F47]' : 'text-[#556B2F]'}`} />
          <span className={`text-sm font-medium ${statusInfo.color === 'red' ? 'text-red-600' : statusInfo.color === 'yellow' ? 'text-[#8B6F47]' : 'text-[#556B2F]'}`}>
            {statusInfo.text}
          </span>
        </div>

        {/* Main Heading */}
        <h2 className="text-2xl font-semibold text-[#5D4037] mb-1">
          {percentageUsed.toFixed(1)}% of budget used
        </h2>

        {/* Timeframe Label */}
        <p className="text-xs uppercase tracking-wider text-[#556B2F]/60 mb-4">
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
            <p className="text-4xl font-bold text-[#5D4037]">{percentageUsed.toFixed(1)}%</p>
            <p className="text-sm text-[#556B2F]">Used</p>
          </div>
        </div>

        {/* Debt Concern Alert */}
        {status === 'debt_concern' && tracking.debt_exceeds_funds && (
          <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <XCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-800 mb-1">Credit Card Debt Exceeds Available Funds</h3>
                <p className="text-sm text-red-700 mb-2">
                  Your credit card debt (${tracking.credit_card_debt?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'}) 
                  exceeds your available funds (${tracking.available_funds?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'}). 
                  Consider creating a debt repayment plan.
                </p>
                <p className="text-sm text-red-700 font-medium">
                  See Recommendations tab for debt payoff timeline and strategies.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Debt Repayment Priority Note */}
        {tracking.category_breakdown && tracking.category_breakdown['Debt Repayment'] && (
          <div className="bg-[#E8F5E9] border-2 border-[#556B2F] rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-[#556B2F] flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-[#556B2F] mb-1">Debt Repayment Priority</h3>
                <p className="text-sm text-[#5D4037] mb-2">
                  Your budget prioritizes aggressive debt repayment. See Recommendations tab for detailed debt payoff timeline and strategies.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Emergency Fund Progress */}
        {tracking.category_breakdown && tracking.category_breakdown['Emergency Fund'] && (
          <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-blue-800 mb-1">Emergency Fund Progress</h3>
                <p className="text-sm text-blue-700">
                  Building your emergency fund: ${tracking.category_breakdown['Emergency Fund']?.spent?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'} / $1,000 target
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-[#E8F5E9] rounded-lg p-4 border border-[#C8E6C9]">
            <p className="text-xs text-[#556B2F] mb-1">Total Budget</p>
            <p className="text-lg font-bold text-[#5D4037]">
              ${tracking.total_budget?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'}
            </p>
          </div>
          <div className="bg-[#E8F5E9] rounded-lg p-4 border border-[#C8E6C9]">
            <p className="text-xs text-[#556B2F] mb-1">Total Spent</p>
            <p className="text-lg font-bold text-red-600">
              ${tracking.total_spent?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'}
            </p>
          </div>
          <div className="bg-[#E8F5E9] rounded-lg p-4 border border-[#C8E6C9]">
            <p className="text-xs text-[#556B2F] mb-1">Remaining</p>
            <p className={`text-lg font-bold ${remaining >= 0 ? 'text-[#556B2F]' : 'text-red-600'}`}>
              ${Math.abs(remaining).toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </p>
          </div>
        </div>

        {/* Category Breakdown */}
        {tracking.category_breakdown && Object.keys(tracking.category_breakdown).length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-[#5D4037] mb-4">Category Breakdown</h3>
            <div className="space-y-3">
              {Object.entries(tracking.category_breakdown || {})
                .sort((a, b) => {
                  const aBudget = (a[1] as any)?.budget || 0
                  const bBudget = (b[1] as any)?.budget || 0
                  return bBudget - aBudget
                })
                .map(([category, data]: [string, any]) => {
                  const isOver = data.is_over_budget || false
                  const budgetPercent = data.budget_percentage || 0
                  const usedPercent = data.percentage_used || 0
                  
                  return (
                    <div
                      key={category}
                      className={`bg-white rounded-lg p-4 border-2 ${
                        isOver ? 'border-red-300 bg-red-50' : 'border-[#D4C4B0]'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-[#5D4037]">{category}</span>
                            {isOver && (
                              <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                                Over Budget
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-[#556B2F]/70 mt-1">
                            {budgetPercent > 0 && `${budgetPercent}% of total budget`}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-[#5D4037]">
                            ${data.budget?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'} budget
                          </div>
                          <div className={`text-sm ${isOver ? 'text-red-600' : 'text-[#556B2F]'}`}>
                            ${data.spent?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '0'} spent
                          </div>
                        </div>
                      </div>
                      
                      {/* Progress Bar */}
                      <div className="w-full bg-[#E8F5E9] rounded-full h-2 mb-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            isOver ? 'bg-red-500' : 'bg-[#556B2F]'
                          }`}
                          style={{
                            width: `${Math.min(usedPercent, 100)}%`
                          }}
                        />
                      </div>
                      
                      <div className="flex justify-between text-xs text-[#556B2F]/70">
                        <span>{usedPercent.toFixed(1)}% used</span>
                        <span className={data.remaining >= 0 ? 'text-[#556B2F]' : 'text-red-600'}>
                          {data.remaining >= 0 ? '+' : ''}$
                          {Math.abs(data.remaining || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}{' '}
                          {data.remaining >= 0 ? 'remaining' : 'over'}
                        </span>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>
        )}

        {/* Summary Text */}
        <p className="text-[#5D4037]/90 text-sm leading-relaxed mt-6">
          {remaining >= 0
            ? `You have $${Math.abs(remaining).toLocaleString('en-US', { maximumFractionDigits: 0 })} remaining this month. Keep up the good work!`
            : `You've exceeded your budget by $${Math.abs(remaining).toLocaleString('en-US', { maximumFractionDigits: 0 })}. Consider adjusting your spending for the remaining days.`
          }
        </p>
      </div>
    </div>
  )
}
